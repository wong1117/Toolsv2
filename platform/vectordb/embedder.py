import httpx
import structlog

logger = structlog.get_logger()

class OllamaEmbedder:
    def __init__(self, ollama_host: str):
        self.url = f"{ollama_host}/api/embeddings"
        self.model = "nomic-embed-text" # Model embedder default Ollama

    async def generate_embedding(self, text: str) -> list[float]:
        """Menghasilkan embedding vector dari teks menggunakan Ollama."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(self.url, json={"model": self.model, "prompt": text})
            response.raise_for_status()
            return response.json().get("embedding", [])
