#!/usr/bin/env python3

"""
Simple test to verify Solana SDK functionality.
"""

from solana.rpc.api import Client
from solders.pubkey import Pubkey

def main():
    print("Testing Solana SDK functionality...")
    
    # Create a client (we won't actually connect to the network)
    client = Client("https://api.mainnet-beta.solana.com")
    print("✓ Solana client created successfully")
    
    # Create a public key
    pubkey = Pubkey.from_string("11111111111111111111111111111111")
    print(f"✓ Public key created: {pubkey}")
    
    print("Solana SDK test completed successfully!")

if __name__ == "__main__":
    main()