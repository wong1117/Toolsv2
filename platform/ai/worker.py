import json
import asyncio
import redis.asyncio as redis
import asyncpg
import structlog
from analyzer import MultiAgentAnalyzer
from vectordb.manager import VectorDBManager
from vectordb.embedder import OllamaEmbedder
from core.config import settings

logger = structlog.get_logger()

class AIWorker:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.analyzer = MultiAgentAnalyzer(ollama_host=settings.OLLAMA_HOST)
        self.vectordb = VectorDBManager(url=settings.QDRANT_URL)
        self.embedder = OllamaEmbedder(ollama_host=settings.OLLAMA_HOST)
        self.queue_name = settings.AI_ANALYSIS_QUEUE_NAME

    async def connect_db(self):
        self.db_pool = await asyncpg.create_pool(dsn=settings.PG_DSN)

    async def _get_context_from_db(self, target_id: str, evidence: dict) -> str:
        """Melakukan RAG untuk mencari konteks kode yang relevan."""
        # 1. Embed query (misalnya file_path + line_start)
        query_text = f"{evidence['location']['file_path']}"
        embedding = await self.embedder.generate_embedding(query_text)
        
        # 2. Cari di Qdrant
        search_result = self.vectordb.client.search(
            collection_name=self.vectordb.collection_name,
            query_vector=embedding,
            query_filter={"must": [{"key": "target_id", "match": {"value": target_id}}]},
            limit=3
        )
        
        # 3. Gabungkan hasil
        context_parts = [hit.payload['content'] for hit in search_result]
        return "\n\n".join(context_parts)

    async def process_queue(self):
        await self.connect_db()
        logger.info("ai_worker_started", queue=self.queue_name)
        
        while True:
            try:
                # 1. Ambil temuan baru dari antrean
                _, message = await self.redis.brpop(self.queue_name)
                payload = json.loads(message)
                fingerprint = payload['fingerprint']
                target_id = payload['target']['target_id']
                
                logger.info("analyzing_finding", fingerprint=fingerprint)
                
                # 2. Ambil konteks kode dari VectorDB (Qdrant)
                context_data = await self._get_context_from_db(target_id, payload['evidence'])
                
                # 3. Jalankan Analisis Multi-Agen
                ai_results = await self.analyzer.run_full_analysis(payload, context_data)
                
                # 4. Simpan hasil AI ke PostgreSQL
                await self._save_ai_results(fingerprint, ai_results)
                
            except Exception as e:
                logger.error("ai_worker_error", error=str(e))

    async def _save_ai_results(self, fingerprint: str, results: dict):
        # Memperbarui status berdasarkan keputusan Ornith
        status = "needs_review"
        if results["triage"].get("is_false_positive"):
            status = "false_positive"
            
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE findings 
                SET status = $1, ai_analysis = $2, updated_at = NOW() 
                WHERE fingerprint = $3
            """, status, json.dumps(results), fingerprint)
            
            await conn.execute("""
                INSERT INTO audit_logs (fingerprint, new_status, changed_by, notes)
                VALUES ($1, $2, 'ai-agent', 'Triage and remediation completed')
            """, fingerprint, status)

if __name__ == "__main__":
    worker = AIWorker()
    asyncio.run(worker.process_queue())
