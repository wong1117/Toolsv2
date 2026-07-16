import asyncio
import json
import httpx
import redis.asyncio as redis
import structlog
import os
import shutil

# Sesuaikan dengan struktur import proyek Anda
from scanners.semgrep_wrapper import SemgrepEngine

logger = structlog.get_logger()

class OrchestratorWorker:
    def __init__(self):
        # Konfigurasi Koneksi
        self.redis = redis.from_url("redis://localhost:6379", decode_responses=True)
        self.queue_name = "scan_jobs"
        self.gateway_ingest_url = "http://localhost:8000/api/ingest" # Endpoint API Gateway kita
        
        # Inisialisasi Scanner
        self.semgrep = SemgrepEngine()
        self.workspace_dir = "/tmp/appsec_workspace"
        
        os.makedirs(self.workspace_dir, exist_ok=True)

    async def _clone_repository(self, repo_url: str, target_id: str) -> str:
        """Simulasi fungsi untuk mengunduh kode sumber via Git."""
        target_path = os.path.join(self.workspace_dir, target_id)
        
        # Dalam produksi, gunakan pustaka GitPython (git.Repo.clone_from)
        logger.info("cloning_repository", repo_url=repo_url, path=target_path)
        
        # Simulasi pembuatan direktori jika Git belum diimplementasikan
        os.makedirs(target_path, exist_ok=True)
        return target_path

    async def _push_to_gateway(self, raw_results: dict, scan_id: str):
        """Mendorong hasil mentah Semgrep ke Gateway Ingestor untuk dinormalisasi."""
        logger.info("pushing_to_gateway", scan_id=scan_id)
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.gateway_ingest_url,
                    json={"scan_id": scan_id, "scanner": "semgrep", "raw_data": raw_results},
                    timeout=60.0
                )
                response.raise_for_status()
            except httpx.HTTPError as e:
                logger.error("gateway_push_failed", error=str(e))
                raise

    async def process_queue(self):
        logger.info("orchestrator_started", queue=self.queue_name)
        
        while True:
            try:
                # 1. Tarik Pekerjaan dari Antrean
                _, message = await self.redis.brpop(self.queue_name)
                job = json.loads(message)
                
                target_id = job['target_id']
                scan_id = job['scan_id']
                repo_url = job['repository_url']
                
                logger.info("processing_scan_job", scan_id=scan_id)
                
                # 2. Siapkan Kode (Clone Git)
                target_path = await self._clone_repository(repo_url, target_id)
                
                # 3. Jalankan Scanner (Berjalan secara sinkron di thread pool agar tidak memblokir loop asinkron)
                raw_results = await asyncio.to_thread(self.semgrep.run_scan, target_path)
                
                # 4. Kirim Hasil ke Gateway Ingestor
                await self._push_to_gateway(raw_results, scan_id)
                
                # 5. Bersihkan Workspace (Opsional, tergantung kebijakan retensi)
                shutil.rmtree(target_path, ignore_errors=True)
                logger.info("scan_job_completed", scan_id=scan_id)
                
            except Exception as e:
                logger.error("scan_job_error", error=str(e))

if __name__ == "__main__":
    worker = OrchestratorWorker()
    asyncio.run(worker.process_queue())
