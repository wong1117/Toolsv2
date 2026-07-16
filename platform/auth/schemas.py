from pydantic import BaseModel
from enum import Enum
from typing import Optional
from uuid import UUID

class RoleEnum(str, Enum):
    VIEWER = "viewer"
    ANALYST = "analyst"
    LEAD = "lead"
    ADMIN = "admin"

class TokenData(BaseModel):
    user_id: UUID
    email: str
    role: RoleEnum

class User(BaseModel):
    id: UUID
    email: str
    role: RoleEnum
    is_active: bool
