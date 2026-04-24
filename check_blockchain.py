"""
check_blockchain.py — Direct blockchain data retrieval script.
Connects to Sepolia and fetches data from the EntryLedger smart contract.
"""
import sys
import os
import json
from web3 import Web3

# 1. Config load karna (Same as your main app)
from config import get_settings
from blockchain.eth_client import EthClient

settings = get_settings()

def fetch_all_blockchain_records():
    print("\nConnecting to Blockchain (Sepolia)... ⛓️")
    
    # Initialize connection
    client = EthClient()
    if not client.w3.is_connected():
        print("❌ Connection failed. Check your internet or INFURA_URL.")
        return

    print(f"✅ Connected! Reading Contract: {settings.CONTRACT_ADDRESS}\n")
    
    # Get total count of entries
    try:
        count = client.contract.functions.getEntryCount().call()
        print(f"🔍 Found {count} total entries on the Ledger.\n")
        print("-" * 80)
        print(f"{'INDEX':<6} | {'ROLL NUMBER':<15} | {'EXAM ID':<15} | {'TIMESTAMP'}")
        print("-" * 80)

        for i in range(count):
            # Har index se data fetch karna
            # returns: (rollNumber, examId, tokenHash, timestamp, recordedBy)
            entry = client.contract.functions.getEntry(i).call()
            
            import datetime
            time_str = datetime.datetime.fromtimestamp(entry[3]).strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"{i:<6} | {entry[0]:<15} | {entry[1]:<15} | {time_str}")

        print("-" * 80)
        print("\nVerification Complete: All records fetched directly from the immutable ledger.")

    except Exception as e:
        print(f"❌ Error reading from contract: {e}")

if __name__ == "__main__":
    fetch_all_blockchain_records()
