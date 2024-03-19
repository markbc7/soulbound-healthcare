// Import ethers from Hardhat package
const { ethers } = require("hardhat");

async function main() {
    // Fetch the contract to deploy
    const HealthRecordsSBT = await ethers.getContractFactory("HealthRecordsSBT");
    
    // Deploy the contract
    const healthRecordsSBT = await HealthRecordsSBT.deploy();

    // Wait for 100 seconds before getting the contract address
    await new Promise(resolve => setTimeout(resolve, 100000));

    // The contract is already deployed when the above await resolves
    console.log("HealthRecordsSBT deployed to:", healthRecordsSBT.address);
}

// Call the main function and catch any errors
main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });

