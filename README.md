# 🏥 Health Records SBT (Soulbound Token)

## 📚 Introduction

This project, developed as the final assignment for the "Introduction to Blockchain" course, demonstrates the application of Soulbound Tokens (SBTs) in managing encrypted health records on the Ethereum Sepolia testnet. By leveraging blockchain technology, the system ensures secure, immutable, and decentralized storage of sensitive health information, with access restricted to authorized parties. The deployed smart contract governs the issuance, update, and access permissions of these digital health records.

## 👥 Team Members

- Adithya Shetty
- Rattamet Boonwong
- Pattapon Tanankakorn

## 🎯 Key Features

- **🔒 Decentralized Health Records Management**: The system utilizes blockchain technology to store health records securely and decentrally, eliminating reliance on centralized databases.
- **🔑 Role-Based Access Control**: The smart contract implements role-based access control, assigning specific permissions to different roles (patient, provider, insurer) to ensure that only authorized individuals can access and modify records.
- **🔐 Encryption and Privacy**: Health records are encrypted using robust cryptographic techniques before being stored on IPFS, ensuring data privacy and confidentiality.
- **🌈 Soulbound Tokens**: The project employs Soulbound Tokens (SBTs) to create an immutable association between health records and individuals, preventing unauthorized transfers or tampering.

## 🛠️ Technology Stack

- **🌐 Ethereum Blockchain**: The smart contract is developed and deployed on the Ethereum network, leveraging its security and decentralization features.
- **📂 IPFS**: The InterPlanetary File System (IPFS) is utilized for decentralized storage of encrypted health records.
- **⚙️ Hardhat**: Hardhat, an Ethereum development environment, is employed to streamline the deployment and testing process.
- **🐍 Web3.py**: Python's Web3.py library is used to facilitate interaction with the Ethereum blockchain.
- **🔒 Cryptography**: The Python cryptography library is employed to ensure secure encryption and decryption of health records.

## 📜 Deployed Contract

The smart contract is deployed on the Ethereum Sepolia testnet. You can interact with it using the following address:
[0xcf2b9fed708012002bea046126204f6fb22accfc](https://sepolia.etherscan.io/address/0xcf2b9fed708012002bea046126204f6fb22accfc)

## 🚀 Getting Started

### Prerequisites

- Node.js and npm
- Python 3.x
- An Infura account and project for accessing the Ethereum network
- IPFS running locally or via a remote node

### Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/markbc7/soulbound-healthcare.git
    ```

2. Install Node.js dependencies:
    ```bash
    npm install
    ```

3. Set up environment variables by creating a `.env` file with your Infura endpoint, private key, and Etherscan API key as described in `hardhat.config.js` and `HealthRecordsSBT_demo.py`.

### Running the Project

1. Compile the smart contract:
    ```bash
    npx hardhat compile
    ```

2. Deploy the smart contract to the Sepolia testnet (ensure your `.env` is configured):
    ```bash
    npx hardhat run scripts/deploy.js --network sepolia
    ```

3. Run the Python demo script to interact with the contract:
    ```bash
    python HealthRecordsSBT_demo.py
    ```

## 📖 Usage

The project includes a user-friendly Python demo script that allows you to add, update, and grant access to health records. The script demonstrates how health records are securely stored on IPFS and referenced through Soulbound Tokens on the Ethereum blockchain. Detailed usage instructions and command examples are provided within the `HealthRecordsSBT_demo.py` script.

---

This project serves as a proof-of-concept for leveraging blockchain technology and Soulbound Tokens in the secure management of health records, offering a decentralized and privacy-focused approach to storing and accessing sensitive medical information. 🩺