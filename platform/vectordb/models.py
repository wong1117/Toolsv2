# platform/vectordb/models.py

from pydantic import BaseModel, Field
from typing import List
from uuid import UUID

class VectorPayload(BaseModel):
    """
    Model ini merepresentasikan metadata yang menempel pada vektor di Qdrant.
    """
    target_id: UUID
    artifact_type: str = Field(description="'code_chunk', 'api_spec', atau 'architecture_doc'")
    file_path: str
    content: str
    reference_hash: str
    schema_version: str = "1.0"

class VectorPoint(BaseModel):
    """
    Model ini merepresentasikan satu kesatuan data yang dikirim ke Qdrant.
    """
    id: UUID
    vector: List[float] # Berisi deretan angka hasil embedding [0.012, -0.023, ...]
    payload: VectorPayload
