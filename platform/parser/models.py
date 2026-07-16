from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List
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
    target_id: str
    repository_url: str
    commit_hash: str

class Location(BaseModel):
    file_path: str
    line_start: int
    line_end: Optional[int] = None

class FindingEvidence(BaseModel):
    location: Location
    code_snippet: str
    # Kita tidak menyimpan seluruh raw JSON di sini, 
    # melainkan akan menyimpannya ke MinIO dan merujuk ID-nya.
    raw_artifact_id: Optional[str] = None 

class NormalizedFinding(BaseModel):
    schema_version: str = Field(default="1.0")
    scan_id: str
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
