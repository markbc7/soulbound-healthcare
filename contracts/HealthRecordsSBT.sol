// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/AccessControl.sol";

contract HealthRecordsSBT is AccessControl {
    bytes32 public constant PATIENT_ROLE = keccak256("PATIENT_ROLE");
    bytes32 public constant PROVIDER_ROLE = keccak256("PROVIDER_ROLE");
    bytes32 public constant INSURER_ROLE = keccak256("INSURER_ROLE");

    struct HealthRecord {
        uint256 recordId;
        string recordType;
        uint256 timestamp;
        string ipfsHash;
    }

    mapping(address => HealthRecord[]) private patientRecords;
    mapping(uint256 => address) private recordOwner;
    mapping(uint256 => mapping(address => bool)) private recordAccess;

    uint256 private _recordIdCounter;

    event HealthRecordAdded(uint256 indexed recordId, address indexed patient, string recordType, string ipfsHash);
    event HealthRecordUpdated(uint256 indexed recordId, address indexed patient, string newRecordType, string newIpfsHash);
    event HealthRecordAccessGranted(uint256 indexed recordId, address indexed patient, address recipient);
    event HealthRecordAccessRevoked(uint256 indexed recordId, address indexed patient, address recipient);

    constructor() {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
    }

    modifier onlyPatientOrProvider() {
        require(hasRole(PATIENT_ROLE, msg.sender) || hasRole(PROVIDER_ROLE, msg.sender), "Unauthorized: caller must be a patient or provider");
        _;
    }

    modifier onlyProvider() {
        require(hasRole(PROVIDER_ROLE, msg.sender), "Unauthorized: caller must be a provider");
        _;
    }

    modifier onlyPatient() {
        require(hasRole(PATIENT_ROLE, msg.sender), "Unauthorized: caller must be a patient");
        _;
    }

    modifier onlyPatientOrAdmin() {
        require(hasRole(PATIENT_ROLE, msg.sender) || hasRole(DEFAULT_ADMIN_ROLE, msg.sender), "Unauthorized: caller must be a patient or admin");
        _;
    }

    modifier recordExists(uint256 recordId) {
        require(recordOwner[recordId] != address(0), "Invalid record ID");
        _;
    }

    modifier hasAccess(uint256 recordId) {
        require(recordAccess[recordId][msg.sender], "Unauthorized: no access to this record");
        _;
    }

    function addHealthRecord(string memory recordType, string memory ipfsHash) public onlyPatientOrProvider {
        _recordIdCounter++;
        uint256 recordId = _recordIdCounter;
        HealthRecord memory record = HealthRecord(recordId, recordType, block.timestamp, ipfsHash);
        patientRecords[msg.sender].push(record);
        recordOwner[recordId] = msg.sender;
        recordAccess[recordId][msg.sender] = true;
        emit HealthRecordAdded(recordId, msg.sender, recordType, ipfsHash);
    }

    function updateHealthRecord(uint256 recordId, string memory newRecordType, string memory newIpfsHash)
        public
        onlyProvider
        recordExists(recordId)
        hasAccess(recordId)
    {
        HealthRecord storage record = patientRecords[recordOwner[recordId]][_findIndex(recordOwner[recordId], recordId)];
        record.recordType = newRecordType;
        record.ipfsHash = newIpfsHash;
        record.timestamp = block.timestamp;
        emit HealthRecordUpdated(recordId, recordOwner[recordId], newRecordType, newIpfsHash);
    }

    function grantRecordAccess(address recipient, uint256 recordId)
        public
        onlyPatient
        recordExists(recordId)
    {
        require(recordOwner[recordId] == msg.sender, "Unauthorized: caller is not the owner of this record");
        recordAccess[recordId][recipient] = true;
        emit HealthRecordAccessGranted(recordId, msg.sender, recipient);
    }

    function revokeRecordAccess(address recipient, uint256 recordId)
        public
        onlyPatientOrAdmin
        recordExists(recordId)
    {
        require(recordAccess[recordId][recipient], "No access to revoke");
        recordAccess[recordId][recipient] = false;
        emit HealthRecordAccessRevoked(recordId, msg.sender, recipient);
    }

    function getPatientRecords(address patient) public view returns (HealthRecord[] memory) {
        bool isAuthorized = msg.sender == patient ||
            hasRole(PROVIDER_ROLE, msg.sender) ||
            (hasRole(INSURER_ROLE, msg.sender) && _hasAccessToAnyRecord(patient, msg.sender));

        require(isAuthorized, "Unauthorized: caller must be the patient, a provider, or have explicit access");
        return patientRecords[patient];
    }

    function hasAccessToRecord(uint256 recordId) public view recordExists(recordId) returns (bool) {
        return recordAccess[recordId][msg.sender];
    }

    function _findIndex(address patient, uint256 recordId) private view returns (uint256) {
        HealthRecord[] storage records = patientRecords[patient];
        for (uint256 i = 0; i < records.length; i++) {
            if (records[i].recordId == recordId) {
                return i;
            }
        }
        revert("Record not found");
    }

    function _hasAccessToAnyRecord(address patient, address account) private view returns (bool) {
        HealthRecord[] storage records = patientRecords[patient];
        for (uint256 i = 0; i < records.length; i++) {
            if (recordAccess[records[i].recordId][account]) {
                return true;
            }
        }
        return false;
    }
}
