// Import ethers from Hardhat package
const { ethers } = require("hardhat");

async function main() {
    // Fetch the contract to deploy
    const HealthRecordsSBT = await ethers.getContractFactory("HealthRecordsSBT");
    
    // Deploy the contract
    const healthRecordsSBT = await HealthRecordsSBT.deploy();

    // Wait for the deployment to finish
    await healthRecordsSBT.deployed();

    console.log("HealthRecordsSBT deployed to:", healthRecordsSBT.address);
}

// Call the main function and catch any errors
main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
