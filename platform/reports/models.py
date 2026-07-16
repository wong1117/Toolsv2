from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
from uuid import UUID

class ReportFinding(BaseModel):
    id: UUID
    title: str
    severity: str
    root_cause: str = "N/A"
    remediation_steps: List[str] = []

class SecurityReportData(BaseModel):
    target_id: UUID
    target_url: str
    generated_at: datetime = Field(default_factory=datetime.now)
    total_findings: int
    findings: List[ReportFinding]
