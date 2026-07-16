from fastapi import APIRouter, HTTPException, Depends, Query
import asyncpg
import structlog
from typing import Optional

# Asumsi impor model dari modul internal
from models.review import ReviewSubmission
from auth.dependencies import RequireRole
from auth.schemas import RoleEnum, TokenData

router = APIRouter(prefix="/api/reviews", tags=["Human Review"])
logger = structlog.get_logger()

# Dependensi koneksi database 
# (Dalam lingkungan produksi, ini mengambil koneksi dari Connection Pool aplikasi)
async def get_db():
    # Contoh koneksi statis untuk demonstrasi. 
    # Pada praktiknya, gunakan app.state.db_pool.acquire()
    conn = await asyncpg.connect("postgresql://user:pass@postgres:5432/appsec_db")
    try:
        yield conn
    finally:
        await conn.close()

@router.get("/pending")
async def get_pending_reviews(
    page: int = Query(1, ge=1, description="Nomor halaman"),
    page_size: int = Query(20, ge=1, le=100, description="Jumlah data per halaman"),
    # Minimal VIEWER bisa melihat antrean
    current_user: TokenData = Depends(RequireRole(RoleEnum.VIEWER)),
    conn: asyncpg.Connection = Depends(get_db)
):
    """Mengambil semua temuan yang telah dianalisis AI dan menunggu tinjauan manusia."""
    offset = (page - 1) * page_size
    
    # Query data dengan pagination
    records = await conn.fetch("""
        SELECT id, fingerprint, title, severity, status, created_at 
        FROM findings 
        WHERE status = 'needs_review'
        ORDER BY severity DESC, created_at ASC
        LIMIT $1 OFFSET $2
    """, page_size, offset)
    
    # Hitung total data untuk keperluan pagination di Frontend
    total_count = await conn.fetchval("SELECT COUNT(*) FROM findings WHERE status = 'needs_review'")
    
    return {
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "pending_reviews": [dict(r) for r in records]
    }

@router.get("/{finding_id}")
async def get_review_details(
    finding_id: str, 
    current_user: TokenData = Depends(RequireRole(RoleEnum.VIEWER)),
    conn: asyncpg.Connection = Depends(get_db)
):
    """Mengambil detail lengkap finding termasuk data dari tabel ai_analyses terpisah."""
    # LEFT JOIN untuk memastikan finding tetap muncul meskipun belum selesai dianalisis AI
    record = await conn.fetchrow("""
        SELECT 
            f.id, f.fingerprint, f.title, f.severity, f.status, f.artifact_id,
            a.agent_name, a.confidence_score, a.is_false_positive, a.root_cause_analysis, a.remediation_steps
        FROM findings f
        LEFT JOIN ai_analyses a ON f.id = a.finding_id
        WHERE f.id = $1
        ORDER BY a.analyzed_at DESC
        LIMIT 1
    """, finding_id)
    
    if not record:
        raise HTTPException(status_code=404, detail="Finding not found")
        
    return dict(record)

@router.post("/{finding_id}/verify")
async def verify_finding(
    finding_id: str, 
    submission: ReviewSubmission,
    # HANYA ANALYST (atau Lead/Admin) yang boleh memverifikasi kerentanan
    current_user: TokenData = Depends(RequireRole(RoleEnum.ANALYST)), 
    conn: asyncpg.Connection = Depends(get_db)
):
    """Memproses keputusan akhir dari analis keamanan dan mencatat Audit Log."""
    
    # Validasi otorisasi payload vs token (mencegah pemalsuan identitas review)
    if str(current_user.user_id) != submission.analyst_id:
         raise HTTPException(status_code=403, detail="Cannot submit review on behalf of another analyst")
         
    log = logger.bind(finding_id=finding_id, analyst_id=submission.analyst_id)
    
    # Menjalankan update dan logging dalam satu transaksi atomik
    async with conn.transaction():
        # 1. Pastikan finding ada dan kuncinya untuk mencegah Race Condition (FOR UPDATE)
        current_status = await conn.fetchval(
            "SELECT status FROM findings WHERE id = $1 FOR UPDATE", finding_id
        )
        
        if not current_status:
            raise HTTPException(status_code=404, detail="Finding not found")
        if current_status != 'needs_review':
            raise HTTPException(status_code=400, detail=f"Finding is currently '{current_status}', expected 'needs_review'")

        # 2. Perbarui status finding
        await conn.execute("""
            UPDATE findings 
            SET status = $1, updated_at = NOW() 
            WHERE id = $2
        """, submission.action.value, finding_id)
        
        # 3. Catat rekam jejak audit (Audit Trail)
        await conn.execute("""
            INSERT INTO audit_logs (finding_id, actor_id, actor_type, previous_status, new_status, comment)
            VALUES ($1, $2, 'human_analyst', $3, $4, $5)
        """, finding_id, str(current_user.user_id), current_status, submission.action.value, submission.notes)
        
    log.info("finding_reviewed_by_human", action=submission.action.value)
    return {"status": "success", "message": "Review submitted successfully"}
