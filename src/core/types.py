"""
Type hints e tipos compartilhados
"""
from typing import TypedDict, Optional, List
from enum import Enum


class FileMetadata(TypedDict):
    """Metadados de arquivo"""
    id: str
    name: str
    size: int
    mimeType: str
    modifiedTime: str
    parents: List[str]


class ProcessingStatus(Enum):
    """Status de processamento"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    VALIDATING = "validating"
    CONVERTING = "converting"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ProcessingResult(TypedDict):
    """Resultado de processamento"""
    file_id: str
    patient_id: str
    status: ProcessingStatus
    input_path: Optional[str]
    output_path: Optional[str]
    error: Optional[str]
    duration_seconds: float
