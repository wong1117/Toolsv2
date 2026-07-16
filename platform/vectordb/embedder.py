import httpx
import structlog
from typing import List

logger = structlog.get_logger()

class OllamaEmbedder:
    def __init__(self, ollama_host: str = "http://localhost:11434"):
        self.ollama_url = ollama_host
        self.model = "nomic-embed-text"  # Model embedding lokal yang sangat efisien
        self.logger = logger.bind(service="ollama_embedder")

    async def generate_embedding(self, text: str) -> List[float]:
        """Mengirim teks ke Ollama dan mengembalikan daftar angka float (vektor)."""
        self.logger.info("generating_embedding", model=self.model)
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.ollama_url}/api/embeddings",
                    json={"model": self.model, "prompt": text},
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                return data["embedding"]
            except Exception as e:
                self.logger.error("embedding_failed", error=str(e))
                raise
