from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import List
from .schemas import TokenData, RoleEnum

# Konfigurasi skema otentikasi FastAPI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Hierarki wewenang (Makin tinggi index, makin besar wewenangnya)
ROLE_HIERARCHY = {
    RoleEnum.VIEWER: 1,
    RoleEnum.ANALYST: 2,
    RoleEnum.LEAD: 3,
    RoleEnum.ADMIN: 4
}

async def get_current_user_token(token: str = Depends(oauth2_scheme)) -> TokenData:
    """
    Di sini Anda akan men-decode JWT dan memvalidasinya.
    (Ini adalah simulasi ekstraksi data dari JWT untuk contoh arsitektur)
    """
    try:
        # Simulasi hasil decode JWT
        # payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # return TokenData(**payload)
        pass 
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

class RequireRole:
    """
    Dependency class untuk membatasi akses berdasarkan hierarki peran.
    """
    def __init__(self, minimum_role: RoleEnum):
        self.minimum_role = minimum_role

    def __call__(self, token_data: TokenData = Depends(get_current_user_token)):
        user_level = ROLE_HIERARCHY.get(token_data.role, 0)
        required_level = ROLE_HIERARCHY.get(self.minimum_role, 99)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to perform this action"
            )
        return token_data
