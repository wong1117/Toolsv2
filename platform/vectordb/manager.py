import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import structlog

# Mengimpor model yang baru saja kita buat di models.py
from .models import VectorPayload

logger = structlog.get_logger()

class VectorDBManager:
    def __init__(self, url: str):
        self.client = QdrantClient(url=url)
        self.collection_name = "target_knowledge"
        self.logger = logger.bind(service="vectordb_manager")

    def init_collection(self, vector_size: int = 1536):
        """Membuat koleksi di Qdrant jika belum ada."""
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )
            self.logger.info("collection_created", collection=self.collection_name)

    async def upsert_chunk(self, payload_data: VectorPayload, embedding: list[float]):
        """Menyimpan vektor dan payload ke Qdrant."""
        point_id = str(uuid.uuid4())
        
        # PointStruct adalah struktur bawaan dari library qdrant_client
        point = PointStruct(
            id=point_id,
            vector=embedding,
            payload=payload_data.model_dump(mode='json') # Mengubah model Pydantic menjadi JSON
        )
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )
        self.logger.info("vector_upserted", point_id=point_id, target_id=str(payload_data.target_id))
