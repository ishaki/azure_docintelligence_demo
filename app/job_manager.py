"""Job status management."""
import logging
from typing import Dict, Optional
from datetime import datetime
from uuid import uuid4

from app.models import JobStatus, FileStatus, FileProcessingResult
from app.constants import STATUS_PENDING, STATUS_PROCESSING, STATUS_COMPLETED, STATUS_ERROR, MESSAGE_QUEUED

logger = logging.getLogger(__name__)


class JobStatusManager:
    """Manages job status tracking."""
    
    def __init__(self) -> None:
        """Initialize the job status manager."""
        self._jobs: Dict[str, JobStatus] = {}
    
    def create_job(self, filenames: list[str]) -> str:
        """
        Create a new job and return its ID.
        
        Args:
            filenames: List of filenames to process
            
        Returns:
            Job ID string
        """
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"
        
        job_status = JobStatus(
            job_id=job_id,
            total_files=len(filenames),
            started_at=datetime.now().isoformat(),
            status=STATUS_PROCESSING,
            files=[
                FileStatus(
                    filename=filename,
                    status=STATUS_PENDING,
                    message=MESSAGE_QUEUED
                )
                for filename in filenames
            ]
        )
        
        self._jobs[job_id] = job_status
        logger.info(f"Created job {job_id} with {len(filenames)} files")
        return job_id
    
    def get_job(self, job_id: str) -> Optional[JobStatus]:
        """
        Get job status by ID.
        
        Args:
            job_id: Job identifier
            
        Returns:
            JobStatus object or None if not found
        """
        return self._jobs.get(job_id)
    
    def update_file_status(
        self,
        job_id: str,
        file_index: int,
        status: str,
        message: str,
        result: Optional[FileProcessingResult] = None
    ) -> None:
        """
        Update status of a file in a job.
        
        Args:
            job_id: Job identifier
            file_index: Index of file in job
            status: New status
            message: Status message
            result: Optional processing result
        """
        if job_id not in self._jobs:
            logger.warning(f"Attempted to update file status for unknown job: {job_id}")
            return
        
        job = self._jobs[job_id]
        if 0 <= file_index < len(job.files):
            job.files[file_index].status = status
            job.files[file_index].message = message
            if result:
                job.files[file_index].result = result
    
    def complete_job(self, job_id: str) -> None:
        """
        Mark a job as completed.
        
        Args:
            job_id: Job identifier
        """
        if job_id in self._jobs:
            self._jobs[job_id].status = STATUS_COMPLETED
            self._jobs[job_id].completed_at = datetime.now().isoformat()
            logger.info(f"Job {job_id} completed")
    
    def delete_job(self, job_id: str) -> None:
        """
        Delete a job from tracking.
        
        Args:
            job_id: Job identifier
        """
        if job_id in self._jobs:
            del self._jobs[job_id]
            logger.info(f"Deleted job {job_id}")


# Global job status manager instance
job_manager = JobStatusManager()

