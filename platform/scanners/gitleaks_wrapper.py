import subprocess
import json
import structlog
from typing import Dict, Any

logger = structlog.get_logger()

class GitleaksEngine:
    def __init__(self):
        self.logger = logger.bind(scanner="gitleaks")

    def run_scan(self, target_path: str) -> Dict[str, Any]:
        """Menjalankan Gitleaks untuk deteksi secret."""
        self.logger.info("starting_scan", target_path=target_path)
        # Gitleaks mendukung output json sejak versi 8.x
        cmd = ["gitleaks", "detect", "--source", target_path, "--report-format", "json", "--no-banner"]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            # Gitleaks mengembalikan exit code 1 jika ada secret ditemukan
            if result.stdout:
                return {"findings": json.loads(result.stdout)} if result.stdout.strip().startswith('[') else {"findings": []}
            return {"findings": []}
        except Exception as e:
            self.logger.error("scan_failed", error=str(e))
            raise
