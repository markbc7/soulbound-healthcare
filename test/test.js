const { expect } = require('chai');
const { ethers } = require("hardhat");

describe("Health Records SBT Contract Tests", function () {
    let healthRecords;
    let admin, patient, provider, insurer, outsider;

    beforeEach(async function () {
        [admin, patient, provider, insurer, outsider] = await ethers.getSigners();
        const HealthRecordsSBT = await ethers.getContractFactory("HealthRecordsSBT");
        healthRecords = await HealthRecordsSBT.deploy();

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
        const tokenId = 0; // Token ID starts from 0
        await healthRecords.connect(patient).grantRecordAccess(provider.address, tokenId, true);
        await expect(healthRecords.connect(provider).updateHealthRecord(tokenId, "Updated Record", "updatedIpfsHash"))
            .to.emit(healthRecords, "HealthRecordUpdated");
    });

    it("Unauthorized accounts cannot grant or revoke access to health records", async function () {
        await healthRecords.connect(patient).addHealthRecord("Record for Access Test", "accessIpfsHash");
        const tokenId = 0;
        await expect(healthRecords.connect(outsider).grantRecordAccess(provider.address, tokenId, true))
            .to.be.revertedWith("Unauthorized: caller must be the patient");
        await expect(healthRecords.connect(outsider).revokeRecordAccess(provider.address, tokenId))
            .to.be.revertedWith("Unauthorized: caller must be the patient or admin");
    });

    it("A patient can grant and then revoke access to their health record", async function () {
        await healthRecords.connect(patient).addHealthRecord("Record for Granting Test", "grantingIpfsHash");
        const tokenId = 0;
        await healthRecords.connect(patient).grantRecordAccess(provider.address, tokenId, true);
        expect(await healthRecords.connect(patient).hasAccessToRecord(tokenId)).to.equal(true);
        await healthRecords.connect(patient).revokeRecordAccess(provider.address, tokenId);
        expect(await healthRecords.connect(provider).hasAccessToRecord(tokenId)).to.equal(false);
    });

    it("Only authorized roles can view health records", async function () {
        await healthRecords.connect(patient).addHealthRecord("Record for Viewing", "viewIpfsHash");
        const tokenId = 0;
        await healthRecords.connect(patient).grantRecordAccess(insurer.address, tokenId, false);
        await expect(healthRecords.connect(insurer).getHealthRecord(tokenId)).to.not.be.reverted;
    });

    it("Providers cannot update health records without explicit access or being the creator", async function () {
        await healthRecords.connect(patient).addHealthRecord("Creator Record", "creatorIpfsHash");
        const tokenId = 0;
        await expect(healthRecords.connect(provider).updateHealthRecord(tokenId, "Unauthorized Update", "newIpfsHash"))
            .to.be.revertedWith("Unauthorized: caller is not the creator of this record or does not have access");
    });

    it("Health record access differentiation between healthcare and insurance providers", async function () {
        await healthRecords.connect(patient).addHealthRecord("Differentiated Access Record", "diffAccessIpfsHash");
        const tokenId = 0;
        await healthRecords.connect(patient).grantRecordAccess(insurer.address, tokenId, false);
        expect(await healthRecords.connect(insurer).hasAccessToRecord(tokenId)).to.equal(true);
    });
});
