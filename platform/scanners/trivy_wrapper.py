import subprocess
import json
import structlog
from typing import Dict, Any

logger = structlog.get_logger()

class TrivyEngine:
    def __init__(self):
        self.logger = logger.bind(scanner="trivy")

    def run_scan(self, target_path: str, scan_type: str = "fs") -> Dict[str, Any]:
        """
        Menjalankan Trivy. Tipe: fs (filesystem), image (container), config (IaC).
        """
        self.logger.info("starting_scan", target_path=target_path, type=scan_type)
        cmd = ["trivy", scan_type, "--format", "json", "--quiet", target_path]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if not result.stdout and result.stderr:
                self.logger.error("trivy_execution_error", detail=result.stderr)
                raise RuntimeError(f"Trivy failed: {result.stderr}")
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            self.logger.error("invalid_json_output")
            raise
