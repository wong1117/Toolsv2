from fastapi import APIRouter, Query
import asyncpg
from core.config import settings
from typing import Optional

router = APIRouter(prefix="/api/review", tags=["Human Review"])

@router.on_event("startup")
async def startup_event():
    router.db_pool = await asyncpg.create_pool(dsn=settings.PG_DSN)

@router.get("/findings")
async def get_findings(
    status: Optional[str] = Query(None, description="Filter by status: needs_review, false_positive, confirmed"),
    limit: int = Query(50, le=100)
):
    """
    Mengambil daftar temuan untuk Human Review Queue.
    Sesuai workflow, ini menampilkan temuan beserta output AI.
    """
    query = """
        SELECT f.fingerprint, f.title, f.severity, f.status, f.created_at, f.ai_analysis
        FROM findings f
        WHERE ($1::text IS NULL OR f.status::text = $1)
        ORDER BY f.created_at DESC
        LIMIT $2;
    """
    async with router.db_pool.acquire() as conn:
        rows = await conn.fetch(query, status, limit)
        
    findings = []
    for row in rows:
        findings.append({
            "fingerprint": row["fingerprint"],
            "title": row["title"],
            "severity": row["severity"],
            "status": row["status"],
            "created_at": str(row["created_at"]),
            "ai_analysis": row["ai_analysis"]  # Sudah berisi JSON hasil kerja AI Worker
        })
        
    return {"total": len(findings), "data": findings}

@router.post("/findings/{fingerprint}/verify")
async def verify_finding(fingerprint: str, payload: dict):
    """
    Endpoint untuk manusia memverifikasi temuan.
    Sesuai workflow: Human Review -> Report & Remediation
    """
    new_status = payload.get("status", "confirmed") # confirmed, fixed, accepted_risk
    reviewer_notes = payload.get("notes", "")
    
    async with router.db_pool.acquire() as conn:
        # Ambil status lama untuk audit log
        old_status = await conn.fetchval("SELECT status FROM findings WHERE fingerprint = $1", fingerprint)
        
        # Update status
        await conn.execute(
            "UPDATE findings SET status = $1, updated_at = NOW() WHERE fingerprint = $2",
            new_status, fingerprint
        )
        
        # Tulis ke Audit Log
        await conn.execute("""
            INSERT INTO audit_logs (fingerprint, previous_status, new_status, changed_by, notes)
            VALUES ($1, $2, $3, 'human-analyst', $4)
        """, fingerprint, old_status, new_status, reviewer_notes)
        
    return {"status": "updated", "fingerprint": fingerprint, "new_status": new_status}
