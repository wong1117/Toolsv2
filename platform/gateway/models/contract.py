from pydantic import BaseModel, Field, AnyUrl
from typing import Optional
from datetime import datetime
from uuid import UUID

class TargetMeta(BaseModel):
    target_id: UUID
    repository_url: Optional[AnyUrl] = None
    commit_hash: str

class Location(BaseModel):
    file_path: str
    line_start: int
    line_end: Optional[int] = None

class FindingEvidence(BaseModel):
    location: Location
    code_snippet: str
    # Menghapus raw_output, kita hanya menyimpan referensi
    raw_artifact_id: Optional[str] = None

class NormalizedFinding(BaseModel):
    schema_version: str = Field(default="1.0")
    scanned_at: datetime
    scan_id: UUID
    scanner_name: str
    target: TargetMeta
    title: str
    severity: str # Tervalidasi melalui skema YAML di parser, di sini terima string
    description: str
    evidence: FindingEvidence
    fingerprint: str
