from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class AnalystAction(str, Enum):
    CONFIRMED = "confirmed"
    FALSE_POSITIVE = "false_positive"
    ACCEPTED_RISK = "accepted_risk"

class ReviewSubmission(BaseModel):
    action: AnalystAction
    analyst_id: str = Field(..., description="UUID analis yang melakukan review")
    notes: str = Field(..., min_length=10, description="Alasan teknis atau catatan verifikasi")
