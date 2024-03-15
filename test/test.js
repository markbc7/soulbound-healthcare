const { expect } = require('chai');
const { ethers } = require("hardhat");

describe("Health Records SBT Contract Tests", function () {
    let healthRecords;
    let admin, patient, provider, insurer, outsider;

    beforeEach(async function () {
        [admin, patient, provider, insurer, outsider] = await ethers.getSigners();
        const HealthRecordsSBT = await ethers.getContractFactory("HealthRecordsSBT");
        healthRecords = await HealthRecordsSBT.deploy();

        // Granting roles after deployment is correct as is
        await healthRecords.grantRole(await healthRecords.PATIENT_ROLE(), patient.address);
        await healthRecords.grantRole(await healthRecords.PROVIDER_ROLE(), provider.address);
        await healthRecords.grantRole(await healthRecords.INSURER_ROLE(), insurer.address);
    });

    it("Only a patient or provider can add a health record", async function () {
        await expect(healthRecords.connect(outsider).addHealthRecord("Test Record", "ipfsHash"))
            .to.be.revertedWith("Unauthorized: caller must be a patient or provider");
        await expect(healthRecords.connect(patient).addHealthRecord("Patient Record", "ipfsHash1"))
            .to.emit(healthRecords, "HealthRecordAdded");
        await expect(healthRecords.connect(provider).addHealthRecord("Provider Record", "ipfsHash2"))
            .to.emit(healthRecords, "HealthRecordAdded");
    });

    it("A provider can update a patient's health record if they have access", async function () {
        await healthRecords.connect(patient).addHealthRecord("Initial Record", "initialIpfsHash");
        // Grant access for the first record (recordId starts from 1)
        await healthRecords.connect(patient).grantRecordAccess(provider.address, 1, true);
        await expect(healthRecords.connect(provider).updateHealthRecord(1, "Updated Record", "updatedIpfsHash"))
            .to.emit(healthRecords, "HealthRecordUpdated");
    });

    it("Unauthorized accounts cannot grant or revoke access to health records", async function () {
        await healthRecords.connect(patient).addHealthRecord("Record for Access Test", "accessIpfsHash");
        await expect(healthRecords.connect(outsider).grantRecordAccess(provider.address, 1, true))
            .to.be.revertedWith("Unauthorized: caller must be a patient");
        await expect(healthRecords.connect(outsider).revokeRecordAccess(provider.address, 1))
            .to.be.revertedWith("Unauthorized: caller must be a patient or admin");
    });

    it("A patient can grant and then revoke access to their health record", async function () {
        await healthRecords.connect(patient).addHealthRecord("Record for Granting Test", "grantingIpfsHash");
        await healthRecords.connect(patient).grantRecordAccess(provider.address, 1, true);
        expect(await healthRecords.connect(patient).hasAccessToRecord(1)).to.equal(true);
        await healthRecords.connect(patient).revokeRecordAccess(provider.address, 1);
        expect(await healthRecords.connect(provider).hasAccessToRecord(1)).to.equal(false);
    });

    it("Only authorized roles can view health records", async function () {
        await healthRecords.connect(patient).addHealthRecord("Record for Viewing", "viewIpfsHash");
        await healthRecords.connect(patient).grantRecordAccess(insurer.address, 1, false);
        // Insurer now tries to view the patient's health records with access
        await healthRecords.connect(insurer).getPatientRecords(patient.address);
    });

    it("Providers cannot update health records without explicit access or being the creator", async function () {
        await healthRecords.connect(patient).addHealthRecord("Creator Record", "creatorIpfsHash");
        await expect(healthRecords.connect(provider).updateHealthRecord(1, "Unauthorized Update", "newIpfsHash"))
            .to.be.revertedWith("Unauthorized: caller is not the creator of this record or does not have access");
    });

    it("Emergency access can be granted to a healthcare provider", async function () {
        await healthRecords.connect(patient).addHealthRecord("Emergency Access Record", "emergencyIpfsHash");
        await expect(healthRecords.connect(provider).useEmergencyAccess(1))
            .to.emit(healthRecords, "EmergencyAccessUsed");
    });

    it("Health record access differentiation between healthcare and insurance providers", async function () {
        await healthRecords.connect(patient).addHealthRecord("Differentiated Access Record", "diffAccessIpfsHash");
        await healthRecords.connect(patient).grantRecordAccess(insurer.address, 1, false);
        expect(await healthRecords.connect(insurer).hasAccessToRecord(1)).to.equal(true);
    });
});
