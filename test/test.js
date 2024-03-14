const { expect } = require('chai');
const { ethers } = require("hardhat");

describe("Health Records SBT Contract Tests", function () {
    let HealthRecordsSBT, healthRecords;
    let admin, patient, provider, insurer, outsider;

    before(async function () {
        [admin, patient, provider, insurer, outsider] = await ethers.getSigners();
        HealthRecordsSBT = await ethers.getContractFactory("HealthRecordsSBT");
        healthRecords = await HealthRecordsSBT.deploy();

        // Granting roles after deployment
        await healthRecords.grantRole(await healthRecords.PATIENT_ROLE(), patient.address);
        await healthRecords.grantRole(await healthRecords.PROVIDER_ROLE(), provider.address);
        await healthRecords.grantRole(await healthRecords.INSURER_ROLE(), insurer.address);
    });

    it("Test case 1: Only a patient or provider can add a health record", async function () {
        // Assuming outsider tries to add a health record
        await expect(healthRecords.connect(outsider).addHealthRecord("Test Record", "ipfsHash"))
            .to.be.revertedWith("Unauthorized: caller must be a patient or provider");
    });

    it("Test case 2: A provider can update a patient's health record", async function () {
        // Ensure a patient adds a record
        await healthRecords.connect(patient).addHealthRecord("Initial Record", "initialIpfsHash");
        // Ensure the provider is granted access if needed by your contract logic
        await healthRecords.connect(patient).grantRecordAccess(provider.address, 1);
        // Provider updates the health record
        await expect(healthRecords.connect(provider).updateHealthRecord(1, "Updated Record", "updatedIpfsHash"))
            .to.emit(healthRecords, "HealthRecordUpdated");
    });

    it("Test case 3: Unauthorized accounts cannot grant or revoke access to health records", async function () {
        // First, a patient adds a health record
        await healthRecords.connect(patient).addHealthRecord("Record for Access Test", "accessIpfsHash");
        // Now, an outsider tries to grant access to another account
        await expect(healthRecords.connect(outsider).grantRecordAccess(provider.address, 1))
            .to.be.revertedWith("Unauthorized: caller must be a patient");
        // Then, an outsider tries to revoke access
        await expect(healthRecords.connect(outsider).revokeRecordAccess(provider.address, 1))
            .to.be.revertedWith("Unauthorized: caller must be a patient or admin");
    });

    it("Test case 4: A patient can grant and then revoke access to their health record", async function () {
        // Patient adds a health record
        await healthRecords.connect(patient).addHealthRecord("Record for Granting Test", "grantingIpfsHash");
        // Patient grants access to the provider
        await healthRecords.connect(patient).grantRecordAccess(provider.address, 1);
        // Check if access was granted successfully
        expect(await healthRecords.connect(provider).hasAccessToRecord(1)).to.be.true;
        // Patient revokes access from the provider
        await healthRecords.connect(patient).revokeRecordAccess(provider.address, 1);
        // Check if access was revoked successfully
        expect(await healthRecords.connect(provider).hasAccessToRecord(1)).to.be.false;
    });

    it("Test case 5: Only authorized roles can view health records", async function () {
      // Patient adds a health record
      await healthRecords.connect(patient).addHealthRecord("Record for Viewing", "viewIpfsHash");
      // Initially, the insurer tries to view the patient's health records without explicit access
      // Expect this attempt to revert due to unauthorized access
      await expect(healthRecords.connect(insurer).getPatientRecords(patient.address))
          .to.be.revertedWith("Unauthorized: caller must be the patient, a provider, or have explicit access");
      // Grant explicit access to the insurer
      await healthRecords.connect(patient).grantRecordAccess(insurer.address, 1);
      // Insurer tries to view the patient's health records again, now with access
      await healthRecords.connect(insurer).getPatientRecords(patient.address);
    });

});
