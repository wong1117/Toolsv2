from typing import List, Dict, Any, Optional
from .base import BaseRepository

class FindingRepository(BaseRepository):
    
    async def get_pending_reviews(self, limit: int, offset: int) -> List[Dict[str, Any]]:
        """Mengambil daftar temuan yang butuh review (dengan pagination)."""
        records = await self.conn.fetch("""
            SELECT id, fingerprint, title, severity, status, created_at 
            FROM findings 
            WHERE status = 'needs_review'
            ORDER BY severity DESC, created_at ASC
            LIMIT $1 OFFSET $2
        """, limit, offset)
        return [dict(r) for r in records]

    async def count_pending_reviews(self) -> int:
        """Menghitung total temuan untuk keperluan pagination."""
        return await self.conn.fetchval("SELECT COUNT(*) FROM findings WHERE status = 'needs_review'")

    async def get_details_with_ai(self, finding_id: str) -> Optional[Dict[str, Any]]:
        """Mengambil detail temuan beserta hasil korelasi agen AI."""
        record = await self.conn.fetchrow("""
            SELECT 
                f.id, f.fingerprint, f.title, f.severity, f.status, f.artifact_id,
                a.agent_name, a.confidence_score, a.is_false_positive, a.root_cause_analysis, a.remediation_steps
            FROM findings f
            LEFT JOIN ai_analyses a ON f.id = a.finding_id
            WHERE f.id = $1
            ORDER BY a.analyzed_at DESC
            LIMIT 1
        """, finding_id)
        return dict(record) if record else None

    async def get_status_for_update(self, finding_id: str) -> Optional[str]:
        """Mengambil status saat ini dan mengunci baris (FOR UPDATE) untuk transaksi atomik."""
        return await self.conn.fetchval(
            "SELECT status FROM findings WHERE id = $1 FOR UPDATE", finding_id
        )

    async def update_status(self, finding_id: str, new_status: str):
        """Memperbarui status temuan."""
        await self.conn.execute("""
            UPDATE findings 
            SET status = $1, updated_at = NOW() 
            WHERE id = $2
        """, new_status, finding_id)
