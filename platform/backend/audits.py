from .base import BaseRepository

class AuditRepository(BaseRepository):
    
    async def create_log(
        self, 
        finding_id: str, 
        actor_id: str, 
        actor_type: str, 
        previous_status: str, 
        new_status: str, 
        comment: str
    ):
        """Menyisipkan rekam jejak baru ke tabel audit_logs."""
        await self.conn.execute("""
            INSERT INTO audit_logs 
            (finding_id, actor_id, actor_type, previous_status, new_status, comment)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, finding_id, actor_id, actor_type, previous_status, new_status, comment)
