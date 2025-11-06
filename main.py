"""
FastAPI application for Azure Document Intelligence integration.

This module provides REST API endpoints for document analysis using Azure
Document Intelligence service.
"""
import asyncio
import logging
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.config import config
from app.document_processor import DocumentProcessor
from app.job_manager import job_manager
from app.models import JobStatus
from app.constants import ALLOWED_FILE_EXTENSIONS, API_PREFIX
from app.logging_config import setup_app_logging

# Setup logging with daily rotation
setup_app_logging()
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Document Intelligence Demo",
    version="1.0.0",
    description="Azure Document Intelligence API for extracting structured data from PDF documents"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    """
    Serve the main HTML page.
    
    Returns:
        HTMLResponse: The index.html page content
    """
    html_path = Path(__file__).parent / "static" / "index.html"
    if html_path.exists():
        logger.debug("Serving index.html")
        return html_path.read_text(encoding="utf-8")
    logger.warning("index.html not found")
    return HTMLResponse(
        content="<h1>Document Intelligence Demo</h1><p>Please create static/index.html</p>",
        status_code=404
    )


@app.post(f"{API_PREFIX}/analyze")
async def analyze_documents(files: List[UploadFile] = File(...)) -> JSONResponse:
    """
    Start async document analysis and return job ID for tracking.
    
    Args:
        files: List of uploaded PDF files
        
    Returns:
        JSONResponse: Contains job_id and total_files for tracking progress
        
    Raises:
        HTTPException: If no files provided or invalid file types
    """
    logger.info(f"Received request to analyze {len(files)} files")
    
    if not files:
        logger.warning("No files provided in request")
        raise HTTPException(
            status_code=400,
            detail="No files provided"
        )
    
    # Validate file types
    invalid_files = [
        file.filename
        for file in files
        if not any(file.filename.lower().endswith(ext) for ext in ALLOWED_FILE_EXTENSIONS)
    ]
    
    if invalid_files:
        logger.warning(f"Invalid file types received: {invalid_files}")
        raise HTTPException(
            status_code=400,
            detail=(
                f"Only {', '.join(ALLOWED_FILE_EXTENSIONS)} files are supported. "
                f"Received invalid files: {', '.join(invalid_files)}"
            )
        )
    
    # Create job
    filenames = [file.filename for file in files]
    job_id = job_manager.create_job(filenames)
    logger.info(f"Created job {job_id} for {len(filenames)} files: {filenames}")
    
    # Read all files content
    files_content = []
    total_size = 0
    for file in files:
        content = await file.read()
        files_content.append((content, file.filename))
        total_size += len(content)
        logger.debug(f"Read file {file.filename}: {len(content)} bytes")
    
    logger.info(f"Total upload size: {total_size} bytes ({total_size / 1024 / 1024:.2f} MB)")
    
    # Start processing asynchronously
    asyncio.create_task(
        DocumentProcessor.process_documents(files_content, job_id)
    )
    
    logger.info(f"Started async processing for job {job_id}")
    
    return JSONResponse(
        content={
            "job_id": job_id,
            "total_files": len(files)
        }
    )


@app.get(f"{API_PREFIX}/status/{{job_id}}")
async def get_status(job_id: str) -> JSONResponse:
    """
    Get processing status for a job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        JSONResponse: Current job status
        
    Raises:
        HTTPException: If job not found
    """
    logger.debug(f"Status request for job {job_id}")
    job = job_manager.get_job(job_id)
    if not job:
        logger.warning(f"Job {job_id} not found")
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )
    
    return JSONResponse(content=job.to_dict())


@app.get(f"{API_PREFIX}/results/{{job_id}}")
async def get_results(job_id: str) -> JSONResponse:
    """
    Get final results for a completed job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        JSONResponse: Processing results or status message
        
    Raises:
        HTTPException: If job not found
    """
    logger.debug(f"Results request for job {job_id}")
    job = job_manager.get_job(job_id)
    if not job:
        logger.warning(f"Job {job_id} not found")
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )
    
    if job.status != "completed":
        logger.debug(f"Job {job_id} still processing")
        return JSONResponse(
            content={
                "status": "processing",
                "message": "Job is still processing"
            },
            status_code=202
        )
    
    # Collect all results
    results = []
    for file_status in job.files:
        if file_status.result:
            result_dict = {
                "filename": file_status.result.filename,
                "status": file_status.result.status,
                "fields": [
                    {
                        "field_name": field.field_name,
                        "field_value": field.field_value,
                        "confidence": field.confidence
                    }
                    for field in file_status.result.fields
                ]
            }
            if file_status.result.error:
                result_dict["error"] = file_status.result.error
            results.append(result_dict)
    
    logger.info(f"Returning results for job {job_id}: {len(results)} files processed")
    return JSONResponse(content={"results": results})


@app.get(f"{API_PREFIX}/health")
async def health_check() -> dict:
    """
    Health check endpoint.
    
    Returns:
        dict: Health status
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=config.host,
        port=config.port
    )
