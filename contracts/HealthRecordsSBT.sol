// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract HealthRecordsSBT is ERC721, AccessControl {
    bytes32 public constant PATIENT_ROLE = keccak256("PATIENT_ROLE");
    bytes32 public constant PROVIDER_ROLE = keccak256("PROVIDER_ROLE");
    bytes32 public constant INSURER_ROLE = keccak256("INSURER_ROLE");

    struct HealthRecord {
        uint256 recordId;
        string recordType;
        uint256 timestamp;
        string ipfsHash;
        address creator;
    }

    mapping(uint256 => HealthRecord) private _healthRecords;
    mapping(uint256 => mapping(address => bool)) private _recordAccess;

    uint256 private _tokenIdCounter;

    event HealthRecordAdded(uint256 indexed tokenId, address indexed patient, string recordType, string ipfsHash);
    event HealthRecordUpdated(uint256 indexed tokenId, address indexed patient, string newRecordType, string newIpfsHash);
    event HealthRecordAccessGranted(uint256 indexed tokenId, address indexed patient, address recipient, string role);
    event HealthRecordAccessRevoked(uint256 indexed tokenId, address indexed patient, address recipient, string role);

    constructor() ERC721("HealthRecordsSBT", "HRSBT") {
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

    modifier onlyPatient(uint256 tokenId) {
        require(ownerOf(tokenId) == msg.sender, "Unauthorized: caller must be the patient");
        _;
    }

    modifier onlyPatientOrAdmin(uint256 tokenId) {
        require(ownerOf(tokenId) == msg.sender || hasRole(DEFAULT_ADMIN_ROLE, msg.sender), "Unauthorized: caller must be the patient or admin");
        _;
    }

    function addHealthRecord(string memory recordType, string memory ipfsHash) public onlyPatientOrProvider {
        uint256 tokenId = _tokenIdCounter;
        _tokenIdCounter++;
        _safeMint(msg.sender, tokenId);
        _healthRecords[tokenId] = HealthRecord(tokenId, recordType, block.timestamp, ipfsHash, msg.sender);
        _recordAccess[tokenId][msg.sender] = true;
        emit HealthRecordAdded(tokenId, msg.sender, recordType, ipfsHash);
    }

    function updateHealthRecord(uint256 tokenId, string memory newRecordType, string memory newIpfsHash) public onlyProvider {
        ownerOf(tokenId);
        require(
            _healthRecords[tokenId].creator == msg.sender || _recordAccess[tokenId][msg.sender],
            "Unauthorized: caller is not the creator of this record or does not have access"
        );
        HealthRecord storage record = _healthRecords[tokenId];
        record.recordType = newRecordType;
        record.ipfsHash = newIpfsHash;
        record.timestamp = block.timestamp;
        emit HealthRecordUpdated(tokenId, ownerOf(tokenId), newRecordType, newIpfsHash);
    }

    function grantRecordAccess(address recipient, uint256 tokenId, bool isHealthcareProvider) public onlyPatient(tokenId) {
        _recordAccess[tokenId][recipient] = true;
        emit HealthRecordAccessGranted(tokenId, msg.sender, recipient, isHealthcareProvider ? "Healthcare Provider" : "Insurance Provider");
    }

    function revokeRecordAccess(address recipient, uint256 tokenId) public onlyPatientOrAdmin(tokenId) {
        require(_recordAccess[tokenId][recipient], "No access to revoke");
        _recordAccess[tokenId][recipient] = false;
        emit HealthRecordAccessRevoked(tokenId, msg.sender, recipient, hasRole(PROVIDER_ROLE, recipient) ? "Healthcare Provider" : "Insurance Provider");
    }

    function getHealthRecord(uint256 tokenId) public view returns (HealthRecord memory) {
        ownerOf(tokenId);
        require(
            ownerOf(tokenId) == msg.sender || hasRole(PROVIDER_ROLE, msg.sender) || hasRole(INSURER_ROLE, msg.sender),
            "Unauthorized: caller must be the patient, a provider, or an insurer"
        );
        return _healthRecords[tokenId];
    }

    function hasAccessToRecord(uint256 tokenId) public view returns (bool) {
        ownerOf(tokenId);
        return _recordAccess[tokenId][msg.sender] || ownerOf(tokenId) == msg.sender;
    }

    function supportsInterface(bytes4 interfaceId) public view virtual override(ERC721, AccessControl) returns (bool) {
        return super.supportsInterface(interfaceId);
    }

    function _beforeTokenTransfer(address from) internal virtual {
        require(from == address(0), "SBT: token transfer not allowed");
    }
}
