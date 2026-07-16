import httpx
import structlog
from core.config import settings

logger = structlog.get_logger()

class MultiAgentAnalyzer:
    def __init__(self, ollama_host: str):
        self.ollama_url = f"{ollama_host}/api/generate"
        # Menggunakan Llama 3 seperti yang disebutkan di arsitektur
        self.model = "llama3" 

    async def _call_ollama(self, prompt: str) -> str:
        """Fungsi bantuan untuk memanggil Ollama API."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(self.ollama_url, json={
                "model": self.model,
                "prompt": prompt,
                "stream": False
            })
            response.raise_for_status()
            return response.json().get("response", "")

    async def run_full_analysis(self, finding_payload: dict, context_data: str) -> dict:
        """
        Menjalankan analisis multi-agen:
        1. Ornith (Triage & False Positive Check)
        2. Qwythos (Root Cause & Remediation)
        """
        fingerprint = finding_payload.get("fingerprint")
        file_path = finding_payload.get("evidence", {}).get("location", {}).get("file_path", "Unknown File")
        
        logger.info("starting_ai_analysis", fingerprint=fingerprint)

        # 1. Agen Ornith: Triage
        triage_prompt = f"""
        Anda adalah agen keamanan siber 'Ornith'. Tugas Anda adalah menilai temuan keamanan.
        Berikut konteks kode terkait:
        --- KODE ---
        {context_data}
        ---------------
        Lokasi File: {file_path}
        
        Apakah temuan ini kemungkinan besar FALSE POSITIVE? Jawab hanya dengan 'YA' atau 'TIDAK', lalu berikan alasan singkat dalam 1 kalimat.
        Format: [YA/TIDAK] - [Alasan]
        """
        triage_response = await self._call_ollama(triage_prompt)
        is_fp = "YA" in triage_response.upper().split()[0]

        # 2. Agen Qwythos: Root Cause & Remediation
        if not is_fp:
            remediation_prompt = f"""
            Anda adalah agen keamanan siber 'Qwythos'. Tugas Anda adalah menganalisis akar masalah dan memberikan rekomendasi perbaikan dan exploit.
            Konteks kode:
            --- KODE ---
            {context_data}
            ---------------
            Berikan output dalam format JSON Valid (tanpa markdown) dengan kunci berikut:
            - "root_cause": (string) Penjelasan teknis mengapa kode ini rentan.
            - "risk_level": (string) Salah satu dari: CRITICAL, HIGH, MEDIUM, LOW.
            - "remediation": (string) Langkah spesifik cara memperbaiki kode tersebut dan exploit.
            """
            qwythos_response = await self._call_ollama(remediation_prompt)
            
            # Fallback sederhana jika LLM gagal mengembalikan JSON yang bersih
            try:
                import json
                qwythos_data = json.loads(qwythos_response.replace("```json", "").replace("```", ""))
            except:
                qwythos_data = {
                    "root_cause": qwythos_response[:200],
                    "risk_level": "MEDIUM",
                    "remediation": "Perlu analisis manual lebih lanjut."
                }
        else:
            qwythos_data = {"root_cause": None, "risk_level": "INFO", "remediation": None}

        return {
            "triage": {
                "is_false_positive": is_fp,
                "reason": triage_response
            },
            "analysis": qwythos_data
        }
