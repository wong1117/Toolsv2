from minio import Minio
from core.config import settings
import json
import uuid
import structlog

logger = structlog.get_logger()

class MinIOClient:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket_name = "artifacts"
        self._ensure_bucket()

    def _ensure_bucket(self):
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)
            logger.info("minio_bucket_created", bucket=self.bucket_name)

    def upload_raw_artifact(self, scan_id: str, raw_data: dict) -> str:
        artifact_id = f"artifacts/{scan_id}/{uuid.uuid4()}.json"
        json_bytes = json.dumps(raw_data).encode('utf-8')
        self.client.put_object(
            self.bucket_name,
            artifact_id,
            data=json_bytes,
            length=len(json_bytes),
            content_type="application/json"
        )
        return artifact_id
