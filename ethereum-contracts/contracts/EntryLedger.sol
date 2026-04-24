// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title EntryLedger
 * @dev Exam entry verification ledger on blockchain
 * Entry once recorded, cannot be modified (immutable)
 */
contract EntryLedger {
    
    address public admin;

    // Entry structure - har exam entry ko define karta hai
    struct Entry {
        string rollNumber;      // Student ka roll number (e.g., "2021CS001")
        string examId;          // Exam ID (e.g., "MIDTERM_2026")
        string tokenHash;       // SHA256 hash of verification token
        uint256 timestamp;      // Entry timestamp (unix)
        address recordedBy;     // Kaun ne record kiya (admin wallet)
    }
    
    // Entries list - sab entries yaha append hote hain
    Entry[] public entries;
    
    // Mapping - token already exist karta hai ya nahi check karne ke liye
    // tokenHash => (index + 1)
    mapping(string => uint256) private tokenToIndex;
    
    // Event - blockchain par Fire hota hai jab entry record ho
    event EntryRecorded(
        string indexed rollNumber,
        string indexed examId,
        string tokenHash,
        uint256 timestamp
    );
    
    constructor() {
        admin = msg.sender;
    }

    /**
     * @dev Entry ko blockchain par record karo
     * @param rollNumber Student roll number
     * @param examId Which exam
     * @param tokenHash SHA256 hash of token
     * @param timestamp Entry timestamp
     */
    function recordEntry(
        string memory rollNumber,
        string memory examId,
        string memory tokenHash,
        uint256 timestamp
    ) public {
        // Duplicate entry check - ek token ek baar hi record ho sakta hai
        require(tokenToIndex[tokenHash] == 0, "Entry already recorded");
        
        // Nayi entry banao aur array mein add karo
        entries.push(Entry(
            rollNumber,
            examId,
            tokenHash,
            timestamp,
            msg.sender
        ));
        
        // Token ko list position set karo (index + 1)
        tokenToIndex[tokenHash] = entries.length;
        
        // Event emit karo - blockchain watchers ko notify karo
        emit EntryRecorded(rollNumber, examId, tokenHash, timestamp);
    }
    
    /**
     * @dev Token hash ke through entry ko verify karo (matches python ABI)
     * @param tokenHash Entry token ka hash
     */
    function verifyEntry(string memory tokenHash)
        public
        view
        returns (
            string memory rollNumber,
            string memory examId,
            uint256 timestamp,
            bool exists
        )
    {
        uint256 idxPlusOne = tokenToIndex[tokenHash];
        if (idxPlusOne > 0) {
            Entry storage e = entries[idxPlusOne - 1];
            return (e.rollNumber, e.examId, e.timestamp, true);
        } else {
            return ("", "", 0, false);
        }
    }
    
    /**
     * @dev Kisi specific entry ko retrieve karo
     * @param index Entry ki position
     */
    function getEntry(uint256 index)
        public
        view
        returns (
            string memory rollNumber,
            string memory examId,
            string memory tokenHash,
            uint256 timestamp,
            address recordedBy
        )
    {
        require(index < entries.length, "Index out of bounds");
        Entry storage e = entries[index];
        return (
            e.rollNumber,
            e.examId,
            e.tokenHash,
            e.timestamp,
            e.recordedBy
        );
    }
    
    /**
     * @dev Total kitne entries hain
     */
    function getEntryCount() public view returns (uint256) {
        return entries.length;
    }
    
    /**
     * @dev Sab entries fetch karo (pagination nahi, sirf small scale ke liye)
     */
    function getAllEntries()
        public
        view
        returns (Entry[] memory)
    {
        return entries;
    }
}
