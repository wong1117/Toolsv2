import json
import redis.asyncio as redis
from core.config import settings

class QueueService:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.queue_name = settings.INGEST_QUEUE_NAME

    async def push_finding(self, finding_data: dict) -> None:
        """Mendorong temuan yang sudah divalidasi ke ekor antrean."""
        payload = json.dumps(finding_data)
        await self.redis.lpush(self.queue_name, payload)

queue_service = QueueService()
