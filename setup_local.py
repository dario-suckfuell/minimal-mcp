#!/usr/bin/env python3
"""
Setup script for local testing environment.
This script helps you create a local environment file for testing.
"""

import os
import shutil


def setup_local_env():
    """Set up local environment file for testing."""
    print("Setting up local environment for MCP Private Database...")
    
    # Check if .env already exists
    if os.path.exists(".env"):
        try:
            response = input(".env already exists. Overwrite? (y/N): ")
            if response.lower() != 'y':
                print("Setup cancelled.")
                return
        except EOFError:
            # Non-interactive environment, skip overwrite
            print(".env already exists. Skipping setup.")
            return
    
    # Copy from example
    if os.path.exists("env.example"):
        shutil.copy("env.example", ".env")
        print("✅ Created .env from env.example")
    else:
        print("❌ env.example not found!")
        return
    
    print("\n📝 Next steps:")
    print("1. Edit .env with your actual API keys:")
    print("   - PINECONE_API_KEY")
    print("   - PINECONE_INDEX") 
    print("   - PINECONE_HOST")
    print("   - OPENAI_API_KEY")
    print("\n2. Configure your embedding model if needed:")
    print("   - EMBEDDING_MODEL (default: text-embedding-3-large)")
    print("   - EMBEDDING_DIMENSIONS (default: 3072)")
    print("\n3. Run the server:")
    print("   make run")
    print("\n4. Test the server:")
    print("   make test")


if __name__ == "__main__":
    setup_local_env()
