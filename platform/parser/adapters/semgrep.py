from enum import Enum
from pydantic import BaseModel, Field, HttpUrl, PositiveInt
from typing import Optional, Literal
from uuid import UUID
from datetime import datetime
import hashlib

class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

class ScannerMeta(BaseModel):
    name: str
    version: str
    rule_id: str

class TargetMeta(BaseModel):
    target_id: UUID
    repository_url: HttpUrl
    commit_hash: str

class Location(BaseModel):
    file_path: str
    line_start: PositiveInt
    line_end: Optional[PositiveInt] = None

class FindingEvidence(BaseModel):
    location: Location
    code_snippet: str
    # Kita tidak menyimpan seluruh raw JSON di sini, 
    # melainkan akan menyimpannya ke MinIO dan merujuk ID-nya.
    raw_artifact_id: Optional[str] = None 

class NormalizedFinding(BaseModel):
    schema_version: Literal["1.0"] = Field(default="1.0")
    scan_id: UUID
    scanned_at: datetime
    scanner: ScannerMeta
    target: TargetMeta
    title: str
    severity: Severity
    description: str
    evidence: FindingEvidence
    
    @property
    def fingerprint(self) -> str:
        """
        Menghasilkan SHA256 unik yang stabil antar pemindaian untuk deduplikasi.
        """
        hash_input = (
            f"{self.scanner.name}:"
            f"{self.scanner.rule_id}:"
            f"{self.evidence.location.file_path}:"
            f"{self.evidence.location.line_start}"
        )
        return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
