"""Data models for the Document Intelligence application."""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class FieldData:
    """Represents a single extracted field."""
    field_name: str
    field_value: str
    confidence: Optional[float] = None


@dataclass
class FileProcessingResult:
    """Result of processing a single file."""
    filename: str
    status: str  # "success" or "error"
    fields: List[FieldData] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class FileStatus:
    """Status of a file being processed."""
    filename: str
    status: str  # "pending", "processing", "completed", "error"
    message: str
    result: Optional[FileProcessingResult] = None


@dataclass
class JobStatus:
    """Status of a document processing job."""
    job_id: str
    total_files: int
    started_at: str
    status: str  # "processing" or "completed"
    files: List[FileStatus] = field(default_factory=list)
    completed_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "job_id": self.job_id,
            "total_files": self.total_files,
            "started_at": self.started_at,
            "status": self.status,
            "files": [
                {
                    "filename": f.filename,
                    "status": f.status,
                    "message": f.message,
                    "result": (
                        {
                            "filename": f.result.filename,
                            "status": f.result.status,
                            "fields": [
                                {
                                    "field_name": field.field_name,
                                    "field_value": field.field_value,
                                    "confidence": field.confidence
                                }
                                for field in f.result.fields
                            ],
                            "error": f.result.error
                        }
                        if f.result else None
                    )
                }
                for f in self.files
            ],
            "completed_at": self.completed_at
        }

