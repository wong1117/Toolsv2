import subprocess
import json
import structlog
from typing import Dict, Any

logger = structlog.get_logger()

class CheckovEngine:
    def __init__(self):
        self.logger = logger.bind(scanner="checkov")

    def run_scan(self, target_path: str) -> Dict[str, Any]:
        """Menjalankan Checkov untuk IaC (Terraform, CloudFormation, K8s, Dockerfile)."""
        self.logger.info("starting_scan", target_path=target_path)
        cmd = ["checkov", "-d", target_path, "--framework", "all", "--output", "json", "--quiet", "--compact", "--skip-check", "CKV_DOCKER_5"]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if not result.stdout:
                return {"results": {"failed_checks": []}}
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            self.logger.error("invalid_json_output")
            return {"results": {"failed_checks": []}}
