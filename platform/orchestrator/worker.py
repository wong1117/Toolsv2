import asyncio
import json
import httpx
import redis.asyncio as redis
import structlog
import os
import shutil
from git import Repo # Menggunakan GitPython yang sudah di-install

from scanners.semgrep_wrapper import SemgrepEngine
from scanners.trivy_wrapper import TrivyEngine
from scanners.gitleaks_wrapper import GitleaksEngine
from scanners.checkov_wrapper import CheckovEngine
from core.config import settings

logger = structlog.get_logger()

class OrchestratorWorker:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.queue_name = settings.SCAN_JOBS_QUEUE
        self.gateway_ingest_url = f"http://{os.getenv('GATEWAY_URL', 'gateway_api:8000')}/api/ingest"
        
        # Inisialisasi Engine Scanner
        self.scanners = {
            "semgrep": SemgrepEngine(),
            "trivy_fs": TrivyEngine(),      # Dependency & Config scan
            "gitleaks": GitleaksEngine(),    # Secret scan
            "checkov": CheckovEngine()       # IaC scan
        }
        self.workspace_dir = "/tmp/appsec_workspace"
        os.makedirs(self.workspace_dir, exist_ok=True)

    def _clone_repository(self, repo_url: str, target_id: str) -> str:
        target_path = os.path.join(self.workspace_dir, target_id)
        if os.path.exists(target_path):
            shutil.rmtree(target_path)
        logger.info("cloning_repository", repo_url=repo_url)
        Repo.clone_from(repo_url, target_path)
        return target_path

    async def _push_to_gateway(self, scan_id: str, scanner_name: str, raw_results: dict):
        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    self.gateway_ingest_url,
                    json={"scan_id": f"{scan_id}-{scanner_name}", "scanner": scanner_name, "raw_data": raw_results},
                    timeout=120.0
                )
            except httpx.HTTPError as e:
                logger.error("gateway_push_failed", scanner=scanner_name, error=str(e))

    async def process_queue(self):
        logger.info("orchestrator_started", queue=self.queue_name)
        while True:
            try:
                _, message = await self.redis.brpop(self.queue_name)
                job = json.loads(message)
                target_id = job['target_id']
                scan_id = job['scan_id']
                repo_url = job['repository_url']
                
                logger.info("processing_scan_job", scan_id=scan_id)

                # 1. Clone repository (Synchronous di threadpool)
                target_path = await asyncio.to_thread(self._clone_repository, repo_url, target_id)

                # 2. Jalankan Multiple Scanners SECARA PARALEL
                tasks = []
                for name, engine in self.scanners.items():
                    # Jalankan scanner sebagai coroutine di thread pool
                    tasks.append(asyncio.to_thread(engine.run_scan, target_path))
                
                # Tunggu semua scanner selesai
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # 3. Kirim semua hasil ke Gateway
                push_tasks = []
                for (name, _), result in zip(self.scanners.items(), results):
                    if isinstance(result, Exception):
                        logger.error("scanner_failed", scanner=name, error=str(result))
                    else:
                        push_tasks.append(self._push_to_gateway(scan_id, name, result))
                
                await asyncio.gather(*push_tasks)

                # 4. Cleanup
                shutil.rmtree(target_path, ignore_errors=True)
                logger.info("scan_job_completed", scan_id=scan_id)

            except Exception as e:
                logger.error("scan_job_error", error=str(e))

if __name__ == "__main__":
    worker = OrchestratorWorker()
    asyncio.run(worker.process_queue())
