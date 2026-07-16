from fastapi import FastAPI
import redis.asyncio as redis
from core.config import settings
import json

app = FastAPI(title="AppSec Gateway API")

@app.on_event("startup")
async def startup_event():
    app.state.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

@app.post("/api/ingest")
async def ingest_raw_scan(payload: dict):
    """
    Menerima raw output dari Orchestrator dan mendorongnya ke antrian Ingestor.
    Payload: {"scan_id": "...", "scanner": "semgrep", "raw_data": {...}}
    """
    await app.state.redis.lpush("ingest_tasks", json.dumps(payload))
    return {"status": "queued_for_processing", "scan_id": payload.get("scan_id")}
