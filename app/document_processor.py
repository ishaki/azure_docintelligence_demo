"""Document processing service."""
import logging
from io import BytesIO
from typing import List, Tuple

from azure.ai.documentintelligence.models import DocumentAnalysisFeature

from app.azure_client import AzureClientFactory
from app.config import config
from app.field_extractor import FieldExtractor
from app.job_manager import job_manager
from app.models import FileProcessingResult
from app.constants import (
    STATUS_PROCESSING,
    STATUS_COMPLETED,
    STATUS_ERROR,
    CONTENT_TYPE_PDF,
    MESSAGE_UPLOADING,
    MESSAGE_SENDING,
    MESSAGE_CALLING_API,
    MESSAGE_WAITING,
    MESSAGE_EXTRACTING,
    MESSAGE_COMPLETED,
    EXPECTED_FIELDS
)

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Service for processing documents with Azure Document Intelligence."""
    
    @staticmethod
    async def process_document(
        file_content: bytes,
        filename: str,
        job_id: str,
        file_index: int
    ) -> None:
        """
        Process a single document and update job status.
        
        Args:
            file_content: Binary content of the PDF file
            filename: Name of the file
            job_id: Job identifier
            file_index: Index of file in job
        """
        client = None
        try:
            # Update status: Starting
            job_manager.update_file_status(
                job_id=job_id,
                file_index=file_index,
                status=STATUS_PROCESSING,
                message=MESSAGE_UPLOADING
            )
            
            # Get async client
            client = AzureClientFactory.create_async_client()
            
            # Convert file content to BytesIO
            file_stream = BytesIO(file_content)
            file_stream.seek(0)
            
            # Update status: Analyzing
            job_manager.update_file_status(
                job_id=job_id,
                file_index=file_index,
                status=STATUS_PROCESSING,
                message=MESSAGE_SENDING
            )
            
            # Update status: Calling API
            job_manager.update_file_status(
                job_id=job_id,
                file_index=file_index,
                status=STATUS_PROCESSING,
                message=MESSAGE_CALLING_API
            )
            
            # Call Azure API
            model_id = config.azure_model_id
            
            if model_id.startswith("prebuilt-"):
                poller = await client.begin_analyze_document(
                    model_id=model_id,
                    body=file_stream,
                    content_type=CONTENT_TYPE_PDF,
                    features=[
                        DocumentAnalysisFeature.KEY_VALUE_PAIRS,
                        DocumentAnalysisFeature.QUERY_FIELDS
                    ],
                    query_fields=EXPECTED_FIELDS
                )
            else:
                poller = await client.begin_analyze_document(
                    model_id=model_id,
                    body=file_stream,
                    content_type=CONTENT_TYPE_PDF
                )
            
            # Poll for results
            job_manager.update_file_status(
                job_id=job_id,
                file_index=file_index,
                status=STATUS_PROCESSING,
                message=MESSAGE_WAITING
            )
            
            analyze_result = await poller.result()
            
            # Extract fields
            job_manager.update_file_status(
                job_id=job_id,
                file_index=file_index,
                status=STATUS_PROCESSING,
                message=MESSAGE_EXTRACTING
            )
            
            fields = FieldExtractor.extract_fields(analyze_result)
            
            # Create result
            result = FileProcessingResult(
                filename=filename,
                status="success",
                fields=fields
            )
            
            # Update status: Complete
            job_manager.update_file_status(
                job_id=job_id,
                file_index=file_index,
                status=STATUS_COMPLETED,
                message=MESSAGE_COMPLETED,
                result=result
            )
            
            logger.info(f"Successfully processed file {filename} in job {job_id}")
            
        except Exception as e:
            logger.error(f"Error processing file {filename}: {str(e)}", exc_info=True)
            
            # Create error result
            result = FileProcessingResult(
                filename=filename,
                status="error",
                error=str(e)
            )
            
            # Update status: Error
            job_manager.update_file_status(
                job_id=job_id,
                file_index=file_index,
                status=STATUS_ERROR,
                message=str(e),
                result=result
            )
        
        finally:
            # Close async client
            if client:
                await client.close()
    
    @staticmethod
    async def process_documents(
        files_content: List[Tuple[bytes, str]],
        job_id: str
    ) -> None:
        """
        Process all documents asynchronously.
        
        Args:
            files_content: List of tuples (content, filename)
            job_id: Job identifier
        """
        import asyncio
        
        tasks = [
            DocumentProcessor.process_document(
                file_content=content,
                filename=filename,
                job_id=job_id,
                file_index=index
            )
            for index, (content, filename) in enumerate(files_content)
        ]
        
        # Process all files concurrently
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Mark job as complete
        job_manager.complete_job(job_id)
        logger.info(f"Completed processing job {job_id}")

