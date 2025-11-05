#!/usr/bin/env python
"""
Startup script for the Document Intelligence Demo application.
"""
import sys
import os
from pathlib import Path

def check_env_file():
    """Check if .env file exists."""
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        print("WARNING: .env file not found!")
        print("Please create a .env file with your Azure credentials.")
        print("See .env.example for reference.")
        print()
        response = input("Do you want to continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)

def main():
    """Main entry point."""
    print("=" * 60)
    print("Document Intelligence Demo - Starting Application")
    print("=" * 60)
    print()
    
    check_env_file()
    
    print("Starting server on http://localhost:8000")
    print("Press Ctrl+C to stop the server")
    print()
    
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()

