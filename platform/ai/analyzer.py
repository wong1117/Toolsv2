import httpx
import json
import structlog
from typing import Dict, Any

logger = structlog.get_logger()

class MultiAgentAnalyzer:
    def __init__(self, ollama_host: str = "http://localhost:11434"):
        self.ollama_url = ollama_host
        self.logger = logger.bind(service="multi_agent_analyzer")

    async def _call_agent(self, agent_name: str, prompt_data: str) -> Dict[str, Any]:
        """Memanggil agen Ollama tertentu dengan format JSON."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": agent_name, # Memanggil 'ornith' atau 'qwythos'
                    "prompt": prompt_data,
                    "format": "json", 
                    "stream": False
                },
                timeout=300.0 # Timeout lebih panjang untuk LLM
            )
            response.raise_for_status()
            raw_text = response.json()["response"]
            return json.loads(raw_text)

    async def run_full_analysis(self, finding_data: Dict[str, Any], retrieved_context: str) -> Dict[str, Any]:
        title = finding_data.get('title', 'Unknown')
        
        # Susun data mentah untuk dikirim ke agen
        payload = f"TITLE: {title}\nDESC: {finding_data.get('description', '')}\nCONTEXT: {retrieved_context}"
        
        # 1. Eksekusi Agen Ornith (Triage)
        self.logger.info("running_ornith_triage", finding_title=title)
        triage_result = await self._call_agent("ornith", payload)
        
        remediation_result = None
        
        # 2. Jika valid, Eksekusi Agen Qwythos (PoC & Remediasi)
        if not triage_result.get("is_false_positive", True):
            self.logger.info("running_qwythos_remediation", finding_title=title)
            poc_payload = f"TITLE: {title}\nROOT CAUSE: {triage_result.get('root_cause_analysis', '')}\nCONTEXT: {retrieved_context}"
            remediation_result = await self._call_agent("qwythos", poc_payload)
            
        return {
            "triage": triage_result,
            "remediation": remediation_result
        }
