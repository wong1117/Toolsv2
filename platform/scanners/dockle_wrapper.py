import subprocess
import json
import structlog
from typing import Dict, Any

logger = structlog.get_logger()

class DockleEngine:
    def __init__(self):
        self.logger = logger.bind(scanner="dockle")

    def run_scan(self, image_name: str) -> Dict[str, Any]:
        """Menjalankan Dockle untuk Container Image Linting."""
        self.logger.info("starting_scan", image=image_name)
        cmd = ["dockle", "--exit-code", "0", "--format", "json", image_name]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if not result.stdout:
                return {"findings": []}
            return json.loads(result.stdout)
        except Exception as e:
            self.logger.error("scan_failed", error=str(e))
            return {"findings": []}
