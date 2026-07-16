import asyncpg

class BaseRepository:
    """
    Kelas dasar untuk semua repositori. 
    Menerima instance koneksi asyncpg saat diinisialisasi.
    """
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn
