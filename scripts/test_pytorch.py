#!/usr/bin/env python3

"""
Simple test to verify PyTorch functionality.
"""

import torch

def main():
    print("Testing PyTorch functionality...")
    
    # Create a simple tensor
    x = torch.tensor([1, 2, 3])
    y = torch.tensor([4, 5, 6])
    
    # Perform a simple operation
    z = x + y
    
    print(f"Tensor x: {x}")
    print(f"Tensor y: {y}")
    print(f"Sum z = x + y: {z}")
    
    # Check if CUDA is available (it won't be in our CPU installation)
    print(f"CUDA available: {torch.cuda.is_available()}")
    
    print("PyTorch test completed successfully!")

if __name__ == "__main__":
    main()