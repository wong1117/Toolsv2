from fastapi import APIRouter, HTTPException, BackgroundTasks, Header
from models.contract import NormalizedFinding
from services.queue import queue_service
import structlog
import uuid

router = APIRouter()
logger = structlog.get_logger()

@router.post("/ingest")
async def ingest_vulnerability(
    finding: NormalizedFinding,
    x_correlation_id: str = Header(default_factory=lambda: str(uuid.uuid4()))
):
    # Bind correlation ID ke logger untuk request ini
    log = logger.bind(
        correlation_id=x_correlation_id, 
        scan_id=str(finding.scan_id),
        fingerprint=finding.fingerprint
    )
    
    try:
        # Pydantic sudah otomatis memvalidasi tipe data (UUID, datetime) saat request masuk
        
        # Injeksi correlation ID ke dalam payload untuk dilacak oleh Worker
        finding_dict = finding.model_dump(mode='json')
        finding_dict['_meta'] = {"correlation_id": x_correlation_id}
        
        # Dorong ke Redis
        await queue_service.push_finding(finding_dict)
        
        log.info("finding_queued_successfully", target_id=str(finding.target.target_id))
        
        return {
            "status": "accepted",
            "correlation_id": x_correlation_id,
            "message": "Finding queued for processing"
        }
    except Exception as e:
        log.error("ingestion_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal ingestion error")
