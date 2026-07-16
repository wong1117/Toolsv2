import subprocess
import json
import structlog
from typing import Dict, Any

logger = structlog.get_logger()

class SemgrepEngine:
    def __init__(self):
        self.logger = logger.bind(scanner="semgrep")

    def run_scan(self, target_path: str) -> Dict[str, Any]:
        """
        Menjalankan Semgrep CLI secara lokal pada direktori target.
        Memerlukan instalasi Semgrep di sistem host/container (pip install semgrep).
        """
        self.logger.info("starting_scan", target_path=target_path)
        
        # Perintah CLI: semgrep scan --json --quiet /path/to/code
        cmd = ["semgrep", "scan", "--json", "--quiet", target_path]
        
        try:
            # subprocess dijalankan; capture_output=True menangkap hasil JSON
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            
            # Semgrep mengembalikan exit code 1 jika ada temuan (bukan error eksekusi)
            # Jika stdout kosong dan ada stderr, berarti alat tersebut gagal berjalan
            if not result.stdout and result.stderr:
                self.logger.error("semgrep_execution_error", detail=result.stderr)
                raise RuntimeError(f"Semgrep failed: {result.stderr}")
                
            return json.loads(result.stdout)
            
        except json.JSONDecodeError:
            self.logger.error("invalid_json_output", output=result.stdout[:200])
            raise
        except Exception as e:
            self.logger.error("scan_failed", error=str(e))
            raise
