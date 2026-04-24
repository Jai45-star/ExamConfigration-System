import "@nomicfoundation/hardhat-ethers";
import * as dotenv from "dotenv";

dotenv.config({ path: "../.env" });

export default {
  solidity: "0.8.19",
  networks: {
    sepolia: {
      url: process.env.ETH_NODE_URL || "",
      accounts: process.env.ADMIN_WALLET_PRIVATE_KEY ? [process.env.ADMIN_WALLET_PRIVATE_KEY] : [],
    },
  },
};
