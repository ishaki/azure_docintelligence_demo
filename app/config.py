"""Configuration management for the Document Intelligence application."""
import os
from typing import Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv

from app.constants import (
    ENV_ENDPOINT,
    ENV_KEY,
    ENV_MODEL_ID,
    DEFAULT_MODEL_ID,
    DEFAULT_HOST,
    DEFAULT_PORT
)


class Config:
    """Application configuration."""
    
    def __init__(self) -> None:
        """Initialize configuration by loading environment variables."""
        # Load .env file if it exists
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        else:
            load_dotenv()
    
    @property
    def azure_endpoint(self) -> Optional[str]:
        """Get Azure Document Intelligence endpoint."""
        return os.getenv(ENV_ENDPOINT)
    
    @property
    def azure_key(self) -> Optional[str]:
        """Get Azure Document Intelligence API key."""
        return os.getenv(ENV_KEY)
    
    @property
    def azure_model_id(self) -> str:
        """Get Azure Document Intelligence model ID."""
        return os.getenv(ENV_MODEL_ID, DEFAULT_MODEL_ID)
    
    @property
    def host(self) -> str:
        """Get server host."""
        return os.getenv("HOST", DEFAULT_HOST)
    
    @property
    def port(self) -> int:
        """Get server port."""
        return int(os.getenv("PORT", DEFAULT_PORT))
    
    def validate_azure_credentials(self) -> Tuple[bool, Optional[str]]:
        """
        Validate Azure credentials are configured.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.azure_endpoint:
            return False, (
                f"{ENV_ENDPOINT} environment variable is not set. "
                "Please configure your Azure Document Intelligence endpoint."
            )
        
        if not self.azure_key:
            return False, (
                f"{ENV_KEY} environment variable is not set. "
                "Please configure your Azure Document Intelligence API key."
            )
        
        return True, None


# Global configuration instance
config = Config()

