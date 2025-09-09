#!/usr/bin/env python3

"""
Verification script to check that all dependencies are correctly installed.
"""

def main():
    print("Verifying SolanaLM environment setup...")
    
    # Test imports
    try:
        import torch
        print(f"✓ PyTorch {torch.__version__} imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import PyTorch: {e}")
    
    try:
        from solana.rpc.api import Client
        print("✓ Solana SDK imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import Solana SDK: {e}")
    
    try:
        from transformers import pipeline
        print("✓ Hugging Face Transformers imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import Transformers: {e}")
    
    try:
        import fastapi
        print("✓ FastAPI imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import FastAPI: {e}")
    
    try:
        import numpy as np
        print(f"✓ NumPy {np.__version__} imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import NumPy: {e}")
    
    print("Verification complete!")

if __name__ == "__main__":
    main()