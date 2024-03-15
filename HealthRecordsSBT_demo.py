from web3 import Web3, exceptions
import ipfshttpclient
import requests
from datetime import datetime
import json
import getpass
from dotenv import load_dotenv
import os

# Connect to Sepolia testnet using Infura endpoint
infura_url = os.getenv("INFURA_SEPOLIA_ENDPOINT")
w3 = Web3(Web3.HTTPProvider(infura_url))

# Check if connected to blockchain
if not w3.isConnected():
    print("Failed to connect to Ethereum network.")
    exit()

# Set the deployed contract address and ABI
contract_address = os.getenv("DEPLOYED_CONTRACT_ADDRESS")
with open("HealthRecordsSBT_abi.json", "r") as abi_definition:
    contract_abi = json.load(abi_definition)

# Connect to a local IPFS node
try:
    ipfs_client = ipfshttpclient.connect()
except Exception as e:
    print(f"Failed to connect to IPFS: {e}")
    exit()

# Load the contract
contract = w3.eth.contract(address=contract_address, abi=contract_abi)

def add_health_record(account, private_key):
    record_type = input("Enter the record type: ")
    file_path = input("Enter the file path: ")

    try:
        # Add the file to IPFS
        ipfs_hash = ipfs_client.add(file_path)['Hash']

        tx = contract.functions.addHealthRecord(record_type, ipfs_hash).buildTransaction({
            'from': account,
            'nonce': w3.eth.getTransactionCount(account),
            'gas': 2000000,
            'gasPrice': w3.eth.gas_price
        })

        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        record_id = tx_receipt['logs'][0]['topics'][1]
        print(f"Health record added with ID: {record_id.hex()}")
    except Exception as e:
        print(f"Failed to add health record: {e}")

def update_health_record(account, private_key):
    record_id = int(input("Enter the record ID: "))
    new_record_type = input("Enter the new record type: ")
    new_file_path = input("Enter the new file path: ")

    try:
        # Add the updated file to IPFS
        new_ipfs_hash = ipfs_client.add(new_file_path)['Hash']

        tx = contract.functions.updateHealthRecord(record_id, new_record_type, new_ipfs_hash).buildTransaction({
            'from': account,
            'nonce': w3.eth.getTransactionCount(account),
            'gas': 2000000,
            'gasPrice': w3.eth.gas_price
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
        tx = contract.functions.grantRecordAccess(recipient_account, record_id, is_healthcare_provider).buildTransaction({
            'from': account,
            'nonce': w3.eth.getTransactionCount(account),
            'gas': 2000000,
            'gasPrice': w3.eth.gas_price
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
        tx = contract.functions.revokeRecordAccess(recipient_account, record_id).buildTransaction({
            'from': account,
            'nonce': w3.eth.getTransactionCount(account),
            'gas': 2000000,
            'gasPrice': w3.eth.gas_price
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
        patient_records = contract.functions.getPatientRecords(patient_account).call()

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
    ipfs_hash = input("Enter the IPFS hash: ")
    ipfs_gateway_url = f"https://ipfs.io/ipfs/{ipfs_hash}"

    try:
        response = requests.get(ipfs_gateway_url)
        response.raise_for_status()
        content = response.text
        print(f"Record Content:\n{content}")
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving record content: {e}")

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
        print("7. Exit")

        choice = input("Enter your choice (1-7): ")

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
            print("Exiting the demo.")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
