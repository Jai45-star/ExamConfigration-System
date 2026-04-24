"""
blockchain/contract_interface.py — ABI for the EntryLedger smart contract.
"""

ENTRY_LEDGER_ABI = [
	{
		"inputs": [],
		"stateMutability": "nonpayable",
		"type": "constructor"
	},
	{
		"anonymous": False,
		"inputs": [
			{
				"indexed": True,
				"internalType": "string",
				"name": "rollNumber",
				"type": "string"
			},
			{
				"indexed": True,
				"internalType": "string",
				"name": "examId",
				"type": "string"
			},
			{
				"indexed": False,
				"internalType": "string",
				"name": "tokenHash",
				"type": "string"
			},
			{
				"indexed": False,
				"internalType": "uint256",
				"name": "timestamp",
				"type": "uint256"
			}
		],
		"name": "EntryRecorded",
		"type": "event"
	},
	{
		"inputs": [],
		"name": "admin",
		"outputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "string",
				"name": "rollNumber",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "examId",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "tokenHash",
				"type": "string"
			},
			{
				"internalType": "uint256",
				"name": "timestamp",
				"type": "uint256"
			}
		],
		"name": "recordEntry",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "string",
				"name": "tokenHash",
				"type": "string"
			}
		],
		"name": "verifyEntry",
		"outputs": [
			{
				"internalType": "string",
				"name": "rollNumber",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "examId",
				"type": "string"
			},
			{
				"internalType": "uint256",
				"name": "timestamp",
				"type": "uint256"
			},
			{
				"internalType": "bool",
				"name": "exists",
				"type": "bool"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "index",
				"type": "uint256"
			}
		],
		"name": "getEntry",
		"outputs": [
			{
				"internalType": "string",
				"name": "rollNumber",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "examId",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "tokenHash",
				"type": "string"
			},
			{
				"internalType": "uint256",
				"name": "timestamp",
				"type": "uint256"
			},
			{
				"internalType": "address",
				"name": "recordedBy",
				"type": "address"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "getEntryCount",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	}
]
