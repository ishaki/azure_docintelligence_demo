"""Constants for the Document Intelligence application."""
from typing import List

# Expected field names
EXPECTED_FIELDS: List[str] = [
    "SupplyAddress1",
    "SupplyAddress2",
    "ConsumptionPeriod",
    "AccountNo",
    "FixedEnergyPriceRate",
    "TotalPayWithAllCharges",
    "TotalEnergyCharge"
]

# Environment variable names
ENV_ENDPOINT = "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"
ENV_KEY = "AZURE_DOCUMENT_INTELLIGENCE_KEY"
ENV_MODEL_ID = "AZURE_DOCUMENT_MODEL_ID"

# Default values
DEFAULT_MODEL_ID = "prebuilt-layout"
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000

# File validation
ALLOWED_FILE_EXTENSIONS = {".pdf"}
CONTENT_TYPE_PDF = "application/pdf"

# Job status values
STATUS_PENDING = "pending"
STATUS_PROCESSING = "processing"
STATUS_COMPLETED = "completed"
STATUS_ERROR = "error"

# File processing messages
MESSAGE_QUEUED = "Queued for processing"
MESSAGE_UPLOADING = "Uploading to Azure..."
MESSAGE_SENDING = "Sending to Azure..."
MESSAGE_CALLING_API = "Calling Azure API..."
MESSAGE_WAITING = "Waiting for Azure response..."
MESSAGE_EXTRACTING = "Extracting fields..."
MESSAGE_COMPLETED = "Completed successfully"

# Field value placeholders
NOT_FOUND = "(not found)"
EMPTY = "(empty)"

# API endpoints
API_PREFIX = "/api"

