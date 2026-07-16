from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from core.config import settings
import structlog

logger = structlog.get_logger()

class VectorDBManager:
    def __init__(self, url: str):
        self.client = QdrantClient(url=url)
        self.collection_name = settings.COLLECTION_NAME
        self._init_collection()

    def _init_collection(self):
        """Membuat collection jika belum ada."""
        try:
            self.client.get_collection(self.collection_name)
        except UnexpectedResponse:
            logger.info("creating_qdrant_collection", name=self.collection_name)
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config={"size": 768, "distance": "Cosine"} # Sesuaikan dengan dimensi model embedder
            )
