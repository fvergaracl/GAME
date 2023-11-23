/* eslint-disable @typescript-eslint/no-unsafe-assignment */
import { ApiKeyModel } from "../models/ApiKeyModel";
import { generateApiKey } from "./index";
import dot from "dotenv";

dot.config();

const initDefaultApiKeys = async () => {
  try {
    console.log("Initializing default API keys...");
    const DEFAULT_API_KEYS = process.env["DEFAULT_API_KEYS"];
    if (DEFAULT_API_KEYS == null) {
      throw new Error("DEFAULT_API_KEYS environment variable is not set");
    }
    const defaultApiKeys: { toolName: string }[] = JSON.parse(
      DEFAULT_API_KEYS || "[]"
    );
    for (const apiKeyInfo of defaultApiKeys) {
      const { toolName } = apiKeyInfo;
      const key = generateApiKey();

      const existingApiKey = await ApiKeyModel.findOne({ toolName });
      if (!existingApiKey) {
        const newApiKey = new ApiKeyModel({
          key,
          toolName,
          creationDate: new Date(),
        });
        await newApiKey.save();
        console.log(`Created API key for ${toolName} | Key: ${key}`);
      }
    }
    console.log("Default API keys initialized");
  } catch (error) {
    console.error("Error initializing default API keys:", error);
  }
};

export { initDefaultApiKeys };
