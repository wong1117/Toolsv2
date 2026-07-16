import json
import asyncio
import uuid
import redis.asyncio as redis
import asyncpg
import structlog
from core.config import settings
from storage.minio_client import MinIOClient
from vectordb.manager import VectorDBManager
from vectordb.embedder import OllamaEmbedder
from parser.adapters.semgrep_adapter import SemgrepAdapter

logger = structlog.get_logger()

class IngestorWorker:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.minio = MinIOClient()
        self.vectordb = VectorDBManager(url=settings.QDRANT_URL)
        self.embedder = OllamaEmbedder(ollama_host=settings.OLLAMA_HOST)
        self.adapters = {
            "semgrep": SemgrepAdapter()
            # Tambahkan adapter trivy/gitleaks di sini setelah membuat parse-nya
        }

    async def connect_db(self):
        self.db_pool = await asyncpg.create_pool(dsn=settings.PG_DSN)

    async def _ensure_target_and_scan(self, target_meta: dict, scan_id: str, scanner_name: str):
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO targets (id, repository_url, commit_hash)
                VALUES ($1, $2, $3) ON CONFLICT (id) DO NOTHING
            """, target_meta.get("target_id", str(uuid.uuid4())), target_meta.get("repository_url"), target_meta.get("commit_hash", "latest"))
            
            await conn.execute("""
                INSERT INTO scans (id, target_id, scanner_name, scanned_at)
                VALUES ($1, $2, $3, NOW()) ON CONFLICT (id) DO NOTHING
            """, scan_id, target_meta.get("target_id"), scanner_name)

    async def _save_finding(self, finding, artifact_id: str):
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO findings (fingerprint, scan_id, target_id, title, severity, artifact_id)
                VALUES ($1, $2, $3, $4, $5, $6) ON CONFLICT (fingerprint) DO UPDATE 
                SET artifact_id = EXCLUDED.artifact_id, updated_at = NOW()
            """, finding.fingerprint, finding.scan_id, finding.target.target_id, 
                 finding.title, finding.severity.value, artifact_id)

    async def _store_in_vectordb(self, finding):
        try:
            text_to_embed = f"{finding.title}\n{finding.description}\n{finding.evidence.code_snippet}"
            embedding = await self.embedder.generate_embedding(text_to_embed)
            
            self.vectordb.client.upsert(
                collection_name=self.vectordb.collection_name,
                points=[{
                    "id": finding.fingerprint,
                    "vector": embedding,
                    "payload": {
                        "target_id": finding.target.target_id,
                        "file_path": finding.evidence.location.file_path,
                        "content": text_to_embed
                    }
                }]
            )
        except Exception as e:
            logger.error("vectordb_upsert_failed", error=str(e))

    async def _push_to_ai_queue(self, finding):
        # Format persis yang diminta oleh platform/ai/worker.py
        payload = {
            "fingerprint": finding.fingerprint,
            "target": {"target_id": finding.target.target_id},
            "evidence": {
                "location": {
                    "file_path": finding.evidence.location.file_path
                }
            }
        }
        await self.redis.lpush(settings.AI_ANALYSIS_QUEUE_NAME, json.dumps(payload))

    async def process_queue(self):
        await self.connect_db()
        logger.info("ingestor_worker_started")

        while True:
            _, message = await self.redis.brpop("ingest_tasks")
            payload = json.loads(message)
            scan_id = payload.get("scan_id")
            scanner_name = payload.get("scanner")
            raw_data = payload.get("raw_data")
            
            logger.info("processing_ingestion", scan_id=scan_id, scanner=scanner_name)

            # 1. Upload raw data ke MinIO
            artifact_id = self.minio.upload_raw_artifact(scan_id, raw_data)

            # 2. Parse Data
            adapter = self.adapters.get(scanner_name)
            if not adapter:
                logger.warning("no_adapter_found", scanner=scanner_name)
                continue
            
            target_meta = payload.get("target", {"target_id": str(uuid.uuid4()), "repository_url": "unknown"})
            findings = adapter.parse(raw_data, {**target_meta, "scan_id": scan_id})

            # 3. Simpan ke DB & VectorDB & kirim ke AI
            await self._ensure_target_and_scan(target_meta, scan_id, scanner_name)
            
            for finding in findings:
                await self._save_finding(finding, artifact_id)
                await self._store_in_vectordb(finding)
                await self._push_to_ai_queue(finding)

            logger.info("ingestion_complete", findings_count=len(findings), scan_id=scan_id)

if __name__ == "__main__":
    worker = IngestorWorker()
    asyncio.run(worker.process_queue())
