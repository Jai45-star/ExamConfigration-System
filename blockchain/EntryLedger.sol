// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title EntryLedger
 * @dev Stores hashes of student entry tokens for immutable audit trail.
 */
contract EntryLedger {
    struct Entry {
        string rollNumber;
        string examId;
        string tokenHash;
        uint256 timestamp;
        bool exists;
    }

    mapping(string => Entry) private entries;
    address public admin;

    event EntryRecorded(
        string indexed rollNumber,
        string indexed examId,
        string tokenHash,
        uint256 timestamp
    );

    constructor() {
        admin = msg.sender;
    }

    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can perform this action");
        _;
    }

    /**
     * @dev Records a new exam entry. Reverts if the tokenHash is reused.
     */
    function recordEntry(
        string memory rollNumber,
        string memory examId,
        string memory tokenHash,
        uint256 timestamp
    ) public onlyAdmin {
        require(!entries[tokenHash].exists, "Token hash already recorded");

        entries[tokenHash] = Entry({
            rollNumber: rollNumber,
            examId: examId,
            tokenHash: tokenHash,
            timestamp: timestamp,
            exists: true
        });

        emit EntryRecorded(rollNumber, examId, tokenHash, timestamp);
    }

    /**
     * @dev Verifies if an entry exists and returns details.
     */
    function verifyEntry(string memory tokenHash) public view returns (
        string memory rollNumber,
        string memory examId,
        uint256 timestamp,
        bool exists
    ) {
        Entry memory entry = entries[tokenHash];
        return (entry.rollNumber, entry.examId, entry.timestamp, entry.exists);
    }
}
