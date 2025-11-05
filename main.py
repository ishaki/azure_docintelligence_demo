"""
FastAPI application for Azure Document Intelligence integration.
"""
import os
from io import BytesIO
from typing import List, Dict, Any
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence.aio import DocumentIntelligenceClient as AsyncDocumentIntelligenceClient
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import DocumentAnalysisFeature

# Load environment variables
load_dotenv()

app = FastAPI(title="Document Intelligence Demo", version="1.0.0")

# Store for tracking processing status
processing_status = {}

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


def get_document_intelligence_client() -> DocumentIntelligenceClient:
    """
    Initialize and return Azure Document Intelligence client (sync).
    
    Returns:
        DocumentIntelligenceClient: Configured client instance
        
    Raises:
        HTTPException: If Azure credentials are not configured
    """
    endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")
    
    if not endpoint or not key:
        raise HTTPException(
            status_code=500,
            detail="Azure Document Intelligence credentials not configured. "
                   "Please set AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and "
                   "AZURE_DOCUMENT_INTELLIGENCE_KEY environment variables."
        )
    
    credential = AzureKeyCredential(key)
    return DocumentIntelligenceClient(endpoint=endpoint, credential=credential)


def get_async_document_intelligence_client() -> AsyncDocumentIntelligenceClient:
    """
    Initialize and return async Azure Document Intelligence client.
    
    Returns:
        AsyncDocumentIntelligenceClient: Configured async client instance
        
    Raises:
        HTTPException: If Azure credentials are not configured
    """
    endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")
    
    if not endpoint or not key:
        raise HTTPException(
            status_code=500,
            detail="Azure Document Intelligence credentials not configured. "
                   "Please set AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and "
                   "AZURE_DOCUMENT_INTELLIGENCE_KEY environment variables."
        )
    
    credential = AzureKeyCredential(key)
    return AsyncDocumentIntelligenceClient(endpoint=endpoint, credential=credential)


def extract_fields_from_result(analyze_result: Any) -> List[Dict[str, Any]]:
    """
    Extract field information from Azure Document Intelligence result.
    Handles both structured documents (invoices, receipts) and key-value pairs.
    Prioritizes expected fields: SupplyAddress1, SupplyAddress2, ConsumptionPeriod,
    AccountNo, FixedEnergyPriceRate, TotalPayWithAllCharges, TotalEnergyCharge.
    
    Args:
        analyze_result: Result from Azure Document Intelligence analyze operation
        
    Returns:
        List of dictionaries containing field name, value, and confidence
    """
    fields = []
    expected_fields_set = {
        "SupplyAddress1", "SupplyAddress2", "ConsumptionPeriod", "AccountNo",
        "FixedEnergyPriceRate", "TotalPayWithAllCharges", "TotalEnergyCharge"
    }
    expected_fields_list = [
        "SupplyAddress1", "SupplyAddress2", "ConsumptionPeriod", "AccountNo",
        "FixedEnergyPriceRate", "TotalPayWithAllCharges", "TotalEnergyCharge"
    ]
    found_fields = set()
    
    # First, extract from structured documents (invoices, receipts, etc.)
    # This is where the expected fields should come from when using query_fields
    if hasattr(analyze_result, 'documents') and analyze_result.documents:
        for document in analyze_result.documents:
            if hasattr(document, 'fields') and document.fields:
                # document.fields is a dictionary where keys are field names
                for field_name, field_value in document.fields.items():
                    # Normalize field name for matching (case-insensitive)
                    normalized_field_name = field_name.replace(" ", "").replace("_", "").replace("-", "").lower()
                    
                    # Try to match with expected fields
                    matched_expected_field = None
                    for expected_field in expected_fields_set:
                        normalized_expected = expected_field.replace(" ", "").replace("_", "").replace("-", "").lower()
                        if normalized_field_name == normalized_expected:
                            matched_expected_field = expected_field
                            break
                    
                    # Use matched expected field name if found, otherwise use original
                    field_name_to_use = matched_expected_field if matched_expected_field else field_name
                    
                    field_data = extract_field_data(field_name_to_use, field_value)
                    if field_data:
                        fields.append(field_data)
                        found_fields.add(field_name_to_use)
    
    # Extract key-value pairs (available in most document types)
    if hasattr(analyze_result, 'key_value_pairs') and analyze_result.key_value_pairs:
        for kv_pair in analyze_result.key_value_pairs:
            # Get key content
            key_content = ""
            key_confidence = None
            if hasattr(kv_pair, 'key') and kv_pair.key:
                if hasattr(kv_pair.key, 'content'):
                    key_content = str(kv_pair.key.content).strip()
                elif hasattr(kv_pair.key, 'text'):
                    key_content = str(kv_pair.key.text).strip()
            
            # Get value content
            value_content = ""
            value_confidence = None
            if hasattr(kv_pair, 'value') and kv_pair.value:
                if hasattr(kv_pair.value, 'content'):
                    value_content = str(kv_pair.value.content).strip()
                elif hasattr(kv_pair.value, 'text'):
                    value_content = str(kv_pair.value.text).strip()
            
            # Get confidence from the pair itself or calculate from key/value
            confidence = None
            if hasattr(kv_pair, 'confidence') and kv_pair.confidence is not None:
                confidence = round(kv_pair.confidence * 100, 2)
            elif key_confidence is not None and value_confidence is not None:
                confidence = round(((key_confidence + value_confidence) / 2) * 100, 2)
            elif key_confidence is not None:
                confidence = round(key_confidence * 100, 2)
            elif value_confidence is not None:
                confidence = round(value_confidence * 100, 2)
            
            # Normalize key content for matching (case-insensitive, remove spaces)
            normalized_key = key_content.replace(" ", "").replace("_", "").replace("-", "").lower()
            
            # Check if this key matches any expected field (case-insensitive, flexible matching)
            matched_field = None
            for expected_field in expected_fields_set:
                normalized_expected = expected_field.replace(" ", "").replace("_", "").replace("-", "").lower()
                if normalized_key == normalized_expected or normalized_key.endswith(normalized_expected):
                    matched_field = expected_field
                    break
            
            # If matched an expected field, use the normalized name; otherwise use original key
            field_name_to_use = matched_field if matched_field else key_content
            
            # Add if we have at least a key (value can be empty for some fields)
            if key_content and field_name_to_use not in found_fields:
                fields.append({
                    "field_name": field_name_to_use,
                    "field_value": value_content if value_content else "(empty)",
                    "confidence": confidence
                })
                found_fields.add(field_name_to_use)
    
    # Ensure all expected fields are present (even if empty)
    for expected_field in expected_fields_set:
        if expected_field not in found_fields:
            fields.append({
                "field_name": expected_field,
                "field_value": "(not found)",
                "confidence": None
            })
    
    # Sort fields: expected fields first, then others
    def sort_key(field):
        if field["field_name"] in expected_fields_set:
            return (0, expected_fields_list.index(field["field_name"]))
        return (1, field["field_name"])
    
    fields.sort(key=sort_key)
    
    return fields


def extract_field_data(field_name: str, field_value: Any) -> Dict[str, Any]:
    """Extract data from a field value object."""
    confidence = None
    field_value_str = None
    
    # Get confidence if available
    if hasattr(field_value, 'confidence') and field_value.confidence is not None:
        confidence = round(field_value.confidence * 100, 2)
    
    # Priority 1: Try 'content' first (most reliable, present in all fields)
    if hasattr(field_value, 'content') and field_value.content:
        field_value_str = str(field_value.content).strip()
    
    # Priority 2: Try valueString (camelCase) or value_string (snake_case)
    elif hasattr(field_value, 'valueString') and field_value.valueString:
        field_value_str = str(field_value.valueString).strip()
    elif hasattr(field_value, 'value_string') and field_value.value_string:
        field_value_str = str(field_value.value_string).strip()
    
    # Priority 3: Try other value types
    elif hasattr(field_value, 'valueNumber') and field_value.valueNumber is not None:
        field_value_str = str(field_value.valueNumber)
    elif hasattr(field_value, 'value_number') and field_value.value_number is not None:
        field_value_str = str(field_value.value_number)
    elif hasattr(field_value, 'valueDate') and field_value.valueDate:
        field_value_str = str(field_value.valueDate)
    elif hasattr(field_value, 'value_date') and field_value.value_date:
        field_value_str = str(field_value.value_date)
    elif hasattr(field_value, 'valueTime') and field_value.valueTime:
        field_value_str = str(field_value.valueTime)
    elif hasattr(field_value, 'value_time') and field_value.value_time:
        field_value_str = str(field_value.value_time)
    elif hasattr(field_value, 'valuePhoneNumber') and field_value.valuePhoneNumber:
        field_value_str = str(field_value.valuePhoneNumber)
    elif hasattr(field_value, 'value_phone_number') and field_value.value_phone_number:
        field_value_str = str(field_value.value_phone_number)
    elif hasattr(field_value, 'valueInteger') and field_value.valueInteger is not None:
        field_value_str = str(field_value.valueInteger)
    elif hasattr(field_value, 'value_integer') and field_value.value_integer is not None:
        field_value_str = str(field_value.value_integer)
    elif hasattr(field_value, 'valueCurrency') and field_value.valueCurrency:
        currency = field_value.valueCurrency
        if hasattr(currency, 'amount') and hasattr(currency, 'currencySymbol'):
            field_value_str = f"{currency.currencySymbol}{currency.amount}"
        elif hasattr(currency, 'amount') and hasattr(currency, 'currency_symbol'):
            field_value_str = f"{currency.currency_symbol}{currency.amount}"
        else:
            field_value_str = str(currency)
    elif hasattr(field_value, 'value_currency') and field_value.value_currency:
        currency = field_value.value_currency
        if hasattr(currency, 'amount') and hasattr(currency, 'currencySymbol'):
            field_value_str = f"{currency.currencySymbol}{currency.amount}"
        elif hasattr(currency, 'amount') and hasattr(currency, 'currency_symbol'):
            field_value_str = f"{currency.currency_symbol}{currency.amount}"
        else:
            field_value_str = str(currency)
    elif hasattr(field_value, 'valueAddress') and field_value.valueAddress:
        address = field_value.valueAddress
        if hasattr(address, 'formatted'):
            field_value_str = address.formatted
        else:
            field_value_str = str(address)
    elif hasattr(field_value, 'value_address') and field_value.value_address:
        address = field_value.value_address
        if hasattr(address, 'formatted'):
            field_value_str = address.formatted
        else:
            field_value_str = str(address)
    
    if field_value_str:
        return {
            "field_name": field_name,
            "field_value": field_value_str,
            "confidence": confidence
        }
    return None


def get_content(obj: Any) -> str:
    """Extract content from a key or value object."""
    if hasattr(obj, 'content'):
        return obj.content
    elif hasattr(obj, 'text'):
        return obj.text
    return ""


def get_confidence(obj: Any) -> float:
    """Extract confidence from a key or value object."""
    if hasattr(obj, 'confidence'):
        return obj.confidence
    return None


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main HTML page."""
    html_path = Path(__file__).parent / "static" / "index.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf-8")
    return "<h1>Document Intelligence Demo</h1><p>Please create static/index.html</p>"


async def process_single_document(file_content: bytes, filename: str, model_id: str, job_id: str, file_index: int, total_files: int):
    """Process a single document and update status."""
    client = None
    try:
        # Update status: Starting
        processing_status[job_id]["files"][file_index]["status"] = "processing"
        processing_status[job_id]["files"][file_index]["message"] = "Uploading to Azure..."
        
        # Get async client
        client = get_async_document_intelligence_client()
        
        # Convert file content to BytesIO
        file_stream = BytesIO(file_content)
        file_stream.seek(0)
        
        # Update status: Analyzing
        processing_status[job_id]["files"][file_index]["message"] = "Sending to Azure..."
        
        # Specify expected fields
        expected_fields = [
            "SupplyAddress1", "SupplyAddress2", "ConsumptionPeriod",
            "AccountNo", "FixedEnergyPriceRate", "TotalPayWithAllCharges",
            "TotalEnergyCharge"
        ]
        
        # Call Azure API based on model type (using await for async)
        processing_status[job_id]["files"][file_index]["message"] = "Calling Azure API..."
        
        if model_id.startswith("prebuilt-"):
            poller = await client.begin_analyze_document(
                model_id=model_id,
                body=file_stream,
                content_type="application/pdf",
                features=[
                    DocumentAnalysisFeature.KEY_VALUE_PAIRS,
                    DocumentAnalysisFeature.QUERY_FIELDS
                ],
                query_fields=expected_fields
            )
        else:
            poller = await client.begin_analyze_document(
                model_id=model_id,
                body=file_stream,
                content_type="application/pdf"
            )
        
        # Poll the Azure poller for progress updates (async)
        processing_status[job_id]["files"][file_index]["message"] = "Waiting for Azure response..."
        
        analyze_result = await poller.result()
        
        processing_status[job_id]["files"][file_index]["message"] = "Extracting fields..."
        
        # Extract fields
        fields = extract_fields_from_result(analyze_result)
        
        # Update status: Complete
        processing_status[job_id]["files"][file_index]["status"] = "completed"
        processing_status[job_id]["files"][file_index]["message"] = "Completed successfully"
        processing_status[job_id]["files"][file_index]["result"] = {
            "filename": filename,
            "status": "success",
            "fields": fields
        }
        
    except Exception as e:
        # Update status: Error
        processing_status[job_id]["files"][file_index]["status"] = "error"
        processing_status[job_id]["files"][file_index]["message"] = str(e)
        processing_status[job_id]["files"][file_index]["result"] = {
            "filename": filename,
            "status": "error",
            "error": str(e),
            "fields": []
        }
    finally:
        # Close async client
        if client:
            await client.close()


@app.post("/api/analyze")
async def analyze_documents(files: List[UploadFile] = File(...)):
    """
    Start async document analysis and return job ID for tracking.
    
    Args:
        files: List of uploaded PDF files
        
    Returns:
        JSON with job_id for tracking progress
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    # Validate file types
    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail=f"Only PDF files are supported. Received: {file.filename}"
            )
    
    # Generate job ID
    job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    
    # Initialize processing status
    processing_status[job_id] = {
        "job_id": job_id,
        "total_files": len(files),
        "started_at": datetime.now().isoformat(),
        "status": "processing",
        "files": [
            {
                "filename": file.filename,
                "status": "pending",
                "message": "Queued for processing",
                "result": None
            }
            for file in files
        ]
    }
    
    # Get model ID
    model_id = os.getenv("AZURE_DOCUMENT_MODEL_ID", "prebuilt-layout")
    
    # Read all files content
    files_content = []
    for file in files:
        content = await file.read()
        files_content.append((content, file.filename))
    
    # Start processing asynchronously
    asyncio.create_task(process_documents_async(files_content, job_id, model_id))
    
    return JSONResponse(content={"job_id": job_id, "total_files": len(files)})


async def process_documents_async(files_content: List[tuple], job_id: str, model_id: str):
    """Process all documents asynchronously."""
    tasks = []
    for index, (content, filename) in enumerate(files_content):
        task = process_single_document(
            content, filename, model_id, job_id, index, len(files_content)
        )
        tasks.append(task)
    
    # Process all files concurrently
    await asyncio.gather(*tasks, return_exceptions=True)
    
    # Mark job as complete
    processing_status[job_id]["status"] = "completed"
    processing_status[job_id]["completed_at"] = datetime.now().isoformat()


@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    """Get processing status for a job."""
    if job_id not in processing_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JSONResponse(content=processing_status[job_id])


@app.get("/api/results/{job_id}")
async def get_results(job_id: str):
    """Get final results for a completed job."""
    if job_id not in processing_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_data = processing_status[job_id]
    
    if job_data["status"] != "completed":
        return JSONResponse(
            content={"status": "processing", "message": "Job is still processing"},
            status_code=202
        )
    
    # Collect all results
    results = []
    for file_data in job_data["files"]:
        if file_data["result"]:
            results.append(file_data["result"])
    
    # Clean up job data after retrieval (optional)
    # del processing_status[job_id]
    
    return JSONResponse(content={"results": results})


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

