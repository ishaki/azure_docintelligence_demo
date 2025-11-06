#!/usr/bin/env python
"""
Startup script for the Document Intelligence Demo application.

This script provides a convenient way to start the FastAPI application
with proper environment validation and configuration.
"""
import sys
import logging
from pathlib import Path

from app.config import config
from app.logging_config import setup_app_logging


def check_env_file() -> bool:
    """
    Check if .env file exists and validate Azure credentials.
    
    Returns:
        True if environment is properly configured, False otherwise
    """
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        print("WARNING: .env file not found!")
        print("Please create a .env file with your Azure credentials.")
        print("See .env.example for reference.")
        print()
        response = input("Do you want to continue anyway? (y/n): ")
        if response.lower() != 'y':
            return False
    
    # Validate Azure credentials
    is_valid, error_message = config.validate_azure_credentials()
    if not is_valid:
        print(f"ERROR: {error_message}")
        print()
        response = input("Do you want to continue anyway? (y/n): ")
        if response.lower() != 'y':
            return False
    
    return True


def main() -> None:
    """Main entry point."""
    # Setup logging first
    setup_app_logging()
    logger = logging.getLogger(__name__)
    
    print("=" * 60)
    print("Document Intelligence Demo - Starting Application")
    print("=" * 60)
    print()
    
    logger.info("Starting application initialization")
    
    if not check_env_file():
        logger.error("Environment validation failed")
        sys.exit(1)
    
    logger.info(f"Starting server on http://{config.host}:{config.port}")
    print(f"Starting server on http://{config.host}:{config.port}")
    print("Press Ctrl+C to stop the server")
    print()
    
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()
