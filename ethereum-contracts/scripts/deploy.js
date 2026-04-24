import hre from "hardhat";

async function main() {
    console.log("🚀 Deployment shuru ho raha hai...");
    
    // Contract ka artifact fetch karo
    const EntryLedger = await hre.ethers.getContractFactory("EntryLedger");
    console.log("✅ Contract artifact loaded");
    
    // Deploy karo
    console.log("⏳ Contract deploy ho raha hai...");
    const contract = await EntryLedger.deploy();
    
    // Deployment wait karo (ethers v6)
    await contract.waitForDeployment();
    console.log("✅ Contract deployed successfully!");
    
    // Address print karo
    const address = await contract.getAddress();
    console.log(`\n📍 Contract Address: ${address}`);
    console.log(`   Copy karo aur .env mein paste karo:\n`);
    console.log(`   CONTRACT_ADDRESS=${address}\n`);
    
    // Test karo - nayi entry add karke dekho
    console.log("🧪 Test entry add kar rahe hain...");
    
    const tokenHash = "hash_42_abcdef";
    const tx = await contract.recordEntry(
        "2021CS001",           // rollNumber
        "MIDTERM_2026",        // examId
        tokenHash,             // tokenHash
        Math.floor(Date.now() / 1000)  // timestamp
    );
    
    // Transaction confirm wait karo
    await tx.wait();
    console.log("✅ Test entry recorded on blockchain!");
    
    // Entry retrieve karo aur dekho
    const entry = await contract.verifyEntry(tokenHash);
    console.log("\n📋 Entry Details:");
    console.log(`   Roll Number: ${entry[0]}`);
    console.log(`   Exam ID: ${entry[1]}`);
    console.log(`   Timestamp: ${entry[2]}`);
    console.log(`   Exists: ${entry[3]}\n`);
    
    console.log("\n✨ Deployment aur test complete!");
}

// Main function execute karo aur errors handle karo
main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
