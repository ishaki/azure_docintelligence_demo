"""Azure Document Intelligence client management."""
from typing import Optional
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence.aio import DocumentIntelligenceClient as AsyncDocumentIntelligenceClient
from azure.ai.documentintelligence import DocumentIntelligenceClient
from fastapi import HTTPException

from app.config import config


class AzureClientFactory:
    """Factory for creating Azure Document Intelligence clients."""
    
    @staticmethod
    def create_sync_client() -> DocumentIntelligenceClient:
        """
        Create and return a synchronous Azure Document Intelligence client.
        
        Returns:
            DocumentIntelligenceClient: Configured client instance
            
        Raises:
            HTTPException: If Azure credentials are not configured
        """
        is_valid, error_message = config.validate_azure_credentials()
        if not is_valid:
            raise HTTPException(
                status_code=500,
                detail=error_message
            )
        
        credential = AzureKeyCredential(config.azure_key)
        return DocumentIntelligenceClient(
            endpoint=config.azure_endpoint,
            credential=credential
        )
    
    @staticmethod
    def create_async_client() -> AsyncDocumentIntelligenceClient:
        """
        Create and return an asynchronous Azure Document Intelligence client.
        
        Returns:
            AsyncDocumentIntelligenceClient: Configured async client instance
            
        Raises:
            HTTPException: If Azure credentials are not configured
        """
        is_valid, error_message = config.validate_azure_credentials()
        if not is_valid:
            raise HTTPException(
                status_code=500,
                detail=error_message
            )
        
        credential = AzureKeyCredential(config.azure_key)
        return AsyncDocumentIntelligenceClient(
            endpoint=config.azure_endpoint,
            credential=credential
        )

