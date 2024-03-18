from web3 import Web3, exceptions
import ipfshttpclient
import requests
from datetime import datetime
import json
import getpass
from dotenv import load_dotenv
import os
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64

# Initialize environment variables
load_dotenv()

# Connect to Sepolia testnet using Infura endpoint
infura_url = os.getenv("INFURA_SEPOLIA_ENDPOINT")
w3 = Web3(Web3.HTTPProvider(infura_url))

# Check if connected to blockchain
if not w3.is_connected():
    print("Failed to connect to Ethereum network.")
    exit()

# Load contract
try:
    contract_address = w3.to_checksum_address(os.getenv("DEPLOYED_CONTRACT_ADDRESS"))
    abi_val = os.getenv("ABI_VALUE")
    
    if w3.is_address(contract_address) and abi_val:
        contract = w3.eth.contract(address=contract_address, abi=abi_val)
        print("Contract loaded successfully.")
    else:
        print("Invalid contract address or ABI.")
except Exception as e:
    print(f"Error loading contract: {e}")

# Connect to a local IPFS node
try:
    ipfs_client = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001/http')
except Exception as e:
    print(f"Failed to connect to IPFS: {e}")
    exit()

# Helper functions for encryption and decryption
def derive_key(address):
    """Derive a symmetric key from the Ethereum account address."""
    backend = default_backend()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'fixed_salt',
        iterations=100000,
        backend=backend
    )
    key = kdf.derive(address.encode())
    return key

def encrypt_data(key, data):
    """Encrypt the data using AES."""
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(data) + padder.finalize()
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ct = encryptor.update(padded_data) + encryptor.finalize()
    return base64.urlsafe_b64encode(iv + ct)

def decrypt_data(key, encrypted_data):
    """Decrypt the data using AES."""
    encrypted_data = base64.urlsafe_b64decode(encrypted_data)
    iv, ct = encrypted_data[:16], encrypted_data[16:]
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    pt = decryptor.update(ct) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    data = unpadder.update(pt) + unpadder.finalize()
    return data

# Contract functions

def grant_role_to_account(admin_account, admin_private_key):
    role = input("Enter the role to grant (patient, provider, insurer): ").lower()
    recipient_account = input("Enter the recipient's Ethereum account address: ")
    
    roles = {
        "patient": contract.functions.PATIENT_ROLE().call(),
        "provider": contract.functions.PROVIDER_ROLE().call(),
        "insurer": contract.functions.INSURER_ROLE().call(),
    }

    role_hash = roles.get(role)
    if not role_hash:
        print("Invalid role specified.")
        return

    try:
        tx = contract.functions.grantRole(role_hash, recipient_account).build_transaction({
            'from': admin_account,
            'gas': 500000,
            'gasPrice': w3.to_wei('20', 'gwei'),
            'nonce': w3.eth.get_transaction_count(admin_account),
        })

        signed_tx = w3.eth.account.sign_transaction(tx, admin_private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Role {role} granted successfully to {recipient_account}. Transaction hash: {tx_receipt.transactionHash.hex()}")
    except Exception as e:
        print(f"Failed to grant role: {e}")

def add_health_record(account, private_key):
    record_type = input("Enter the record type: ")
    file_path = input("Enter the file path: ")

    try:
        # Read the file content
        with open(file_path, "rb") as file:
            file_content = file.read()

        # Encrypt the file content
        key = derive_key(account)
        encrypted_content = encrypt_data(key, file_content)

        # Write the encrypted content to a temp file
        temp_file_path = "temp_encrypted"
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(encrypted_content)

        # Add the encrypted file to IPFS
        ipfs_hash = ipfs_client.add(temp_file_path)['Hash']
        os.remove(temp_file_path)  # Clean up the temp file

        # Build the transaction
        tx = contract.functions.addHealthRecord(record_type, ipfs_hash).build_transaction({
            'from': account,
            'gas': 500000,
            'gasPrice': w3.to_wei('10', 'gwei'),
            'nonce': w3.eth.get_transaction_count(account),
            'chainId': w3.eth.chain_id
        })

        # Sign the transaction
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)

        # Send the transaction
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

        # Wait for the transaction to be mined
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        print("Transaction receipt:", tx_receipt.transactionHash.hex())
    except Exception as e:
        print(f"Failed to add health record: {e}")

def update_health_record(account, private_key):
    record_id = int(input("Enter the record ID: "))
    new_record_type = input("Enter the new record type: ")
    new_file_path = input("Enter the new file path: ")

    try:
        # Read the new file content
        with open(new_file_path, "rb") as file:
            file_content = file.read()

        # Encrypt the new file content
        key = derive_key(account)
        encrypted_content = encrypt_data(key, file_content)

        # Write the encrypted content to a temp file
        temp_file_path = "temp_encrypted_update"
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(encrypted_content)

        # Add the encrypted file to IPFS
        new_ipfs_hash = ipfs_client.add(temp_file_path)['Hash']
        os.remove(temp_file_path)  # Clean up the temp file

        # Build and send transaction
        tx = contract.functions.updateHealthRecord(record_id, new_record_type, new_ipfs_hash).build_transaction({
            'from': account,
            'gas': 500000,
            'gasPrice': w3.to_wei('10', 'gwei'),
            'nonce': w3.eth.get_transaction_count(account),
            'chainId': w3.eth.chain_id
        })

        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print("Health record updated successfully.")
    except Exception as e:
        print(f"Failed to update health record: {e}")

def grant_record_access(account, private_key):
    recipient_account = input("Enter the recipient account address: ")
    record_id = int(input("Enter the record ID: "))
    is_healthcare_provider = input("Is the recipient a healthcare provider? (yes/no): ").lower() == 'yes'

    try:
        tx = contract.functions.grantRecordAccess(recipient_account, record_id, is_healthcare_provider).build_transaction({
            'from': account,
            'gas': 500000,
            'gasPrice': w3.to_wei('10', 'gwei'),
            'nonce': w3.eth.get_transaction_count(account),
            'chainId': w3.eth.chain_id
        })

        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print("Record access granted successfully.")
    except Exception as e:
        print(f"Failed to grant record access: {e}")

def revoke_record_access(account, private_key):
    recipient_account = input("Enter the recipient account address: ")
    record_id = int(input("Enter the record ID: "))

    try:
        tx = contract.functions.revokeRecordAccess(recipient_account, record_id).build_transaction({
            'from': account,
            'gas': 500000,
            'gasPrice': w3.to_wei('10', 'gwei'),
            'nonce': w3.eth.get_transaction_count(account),
            'chainId': w3.eth.chain_id
        })

        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print("Record access revoked successfully.")
    except Exception as e:
        print(f"Failed to revoke record access: {e}")

def get_patient_records(account):
    patient_account = input("Enter the patient account address: ")

    try:
        patient_records = contract.functions.getPatientRecords(patient_account).call({'from': account})

        if not patient_records:
            print("No records found.")
        else:
            print("Patient Records:")
            for record in patient_records:
                print(f"Record ID: {record[0]}")
                print(f"Record Type: {record[1]}")
                print(f"Timestamp: {datetime.utcfromtimestamp(record[2]).strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"IPFS Hash: {record[3]}")
                print("---")
    except Exception as e:
        print(f"Failed to get patient records: {e}")

def display_record_content():
    account = input("Enter your Ethereum account address for decryption: ")
    ipfs_hash = input("Enter the IPFS hash: ")

    try:
        file_path = ipfs_client.get(ipfs_hash, './local_files')
        with open(f'./local_files/{ipfs_hash}', 'rb') as file:
            encrypted_content = file.read()

        key = derive_key(account)
        decrypted_content = decrypt_data(key, encrypted_content)
        print(f"Record Content:\n{decrypted_content.decode()}")
    except Exception as e:
        print(f"Error retrieving or decrypting record content: {e}")

def main():
    print("\nHealth Records SBT Demo")
    account = input("Enter your Ethereum account address: ")
    private_key = getpass.getpass(prompt='Enter your private key: ')

    while True:
        print("\nOptions:")
        print("1. Add Health Record")
        print("2. Update Health Record")
        print("3. Grant Record Access")
        print("4. Revoke Record Access")
        print("5. Get Patient Records")
        print("6. Display Record Content")
        print("7. Grant Role to Account")
        print("8. Change User")
        print("9. Exit")

        choice = input("Enter your choice (1-9): ")

        if choice == "1":
            add_health_record(account, private_key)
        elif choice == "2":
            update_health_record(account, private_key)
        elif choice == "3":
            grant_record_access(account, private_key)
        elif choice == "4":
            revoke_record_access(account, private_key)
        elif choice == "5":
            get_patient_records(account)
        elif choice == "6":
            display_record_content()
        elif choice == "7":
            grant_role_to_account(account, private_key)
        elif choice == "8":
            account = input("Enter new Ethereum account address: ")
            private_key = getpass.getpass(prompt='Enter new private key: ')
            print("User changed successfully.")
        elif choice == "9":
            print("Exiting the demo.")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
