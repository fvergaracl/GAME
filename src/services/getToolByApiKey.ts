import { ApiKeyModel } from "../models";

/**
 * Retrieves a user by their API key.
 * @param apiKey The API key to search for.
 * @returns The user if found, otherwise null.
 */
export async function getToolByApiKey(apiKey: string) {
  try {
    const tool = await ApiKeyModel.findOne({ key: apiKey }); // Asumiendo que tus usuarios tienen un campo 'apiKey'
    return tool;
  } catch (error) {
    console.error("Error fetching user by API key:", error);
    return null;
  }
}
