import json
import asyncio
import redis.asyncio as redis
import asyncpg
from minio import Minio
import structlog
from core.config import settings

logger = structlog.get_logger()

class IngestionWorker:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        # MinIO Client (Synchronous, dibungkus async untuk I/O jika perlu)
        self.minio_client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False
        )
        self.bucket_name = "appsec-artifacts"
        
        # Pastikan bucket tersedia
        if not self.minio_client.bucket_exists(self.bucket_name):
            self.minio_client.make_bucket(self.bucket_name)

    async def connect_db(self):
        self.db_pool = await asyncpg.create_pool(dsn=settings.PG_DSN)

    async def process_queue(self):
        await self.connect_db()
        logger.info("worker_started", queue=settings.INGEST_QUEUE_NAME)
        
        while True:
            try:
                # 1. Blocking Pop dari Redis (Tunggu hingga ada pesan masuk)
                _, message = await self.redis.brpop(settings.INGEST_QUEUE_NAME)
                payload = json.loads(message)
                
                # Ekstrak data dan metadata tracing
                meta = payload.pop('_meta', {})
                correlation_id = meta.get('correlation_id', 'unknown')
                
                log = logger.bind(correlation_id=correlation_id, fingerprint=payload['fingerprint'])
                
                # 2. Simpan Bukti (Evidence) ke MinIO
                artifact_id = await self._store_evidence_to_minio(payload)
                
                # 3. Upsert ke PostgreSQL dan catat jejak audit
                await self._upsert_to_postgres(payload, artifact_id, correlation_id, log)
                
            except Exception as e:
                logger.error("worker_processing_error", error=str(e))
                # Dalam skenario produksi, kirim pesan yang gagal ke Dead Letter Queue (DLQ)

    async def _store_evidence_to_minio(self, payload: dict) -> str:
        """Menyimpan dictionary evidence ke Object Storage."""
        scan_id = payload['scan_id']
        fingerprint = payload['fingerprint']
        evidence_data = payload.get('evidence', {})
        
        artifact_id = f"scans/{scan_id}/evidence_{fingerprint}.json"
        evidence_bytes = json.dumps(evidence_data).encode('utf-8')
        
        # Eksekusi sinkron MinIO di dalam thread pool agar tidak memblokir event loop
        await asyncio.to_thread(
            self.minio_client.put_object,
            self.bucket_name, artifact_id,
            data=io.BytesIO(evidence_bytes),
            length=len(evidence_bytes),
            content_type="application/json"
        )
        return artifact_id

    async def _upsert_to_postgres(self, payload: dict, artifact_id: str, correlation_id: str, log):
        """Menyimpan data dengan logika ON CONFLICT untuk deduplikasi otomatis."""
        fingerprint = payload['fingerprint']
        scan_id = payload['scan_id']
        target = payload['target']
        
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                # Pastikan Target & Scan ada (Sederhananya di sini, dalam produksi bisa di-cache)
                await conn.execute(
                    "INSERT INTO targets (id, commit_hash) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                    target['target_id'], target['commit_hash']
                )
                await conn.execute(
                    "INSERT INTO scans (id, target_id, scanner_name, scanned_at) VALUES ($1, $2, $3, $4) ON CONFLICT DO NOTHING",
                    scan_id, target['target_id'], payload['scanner_name'], payload['scanned_at']
                )

                # Upsert Finding
                status_sebelumnya = await conn.fetchval(
                    "SELECT status FROM findings WHERE fingerprint = $1", fingerprint
                )

                if not status_sebelumnya:
                    # Temuan Baru
                    await conn.execute("""
                        INSERT INTO findings (fingerprint, scan_id, target_id, title, severity, status, artifact_id)
                        VALUES ($1, $2, $3, $4, $5, 'new', $6)
                    """, fingerprint, scan_id, target['target_id'], payload['title'], payload['severity'], artifact_id)
                    
                    # Catat ke Audit Log
                    await conn.execute("""
                        INSERT INTO audit_logs (fingerprint, new_status, changed_by, notes, correlation_id)
                        VALUES ($1, 'new', 'system-worker', 'Initial finding ingested', $2)
                    """, fingerprint, correlation_id)
                    
                    log.info("new_finding_inserted")
                else:
                    # Temuan sudah ada, perbarui waktu & referensi scan terbaru
                    await conn.execute("""
                        UPDATE findings SET updated_at = NOW(), scan_id = $2 WHERE fingerprint = $1
                    """, fingerprint, scan_id)
                    log.info("existing_finding_updated")

if __name__ == "__main__":
    worker = IngestionWorker()
    asyncio.run(worker.process_queue())
