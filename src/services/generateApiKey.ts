import { randomBytes } from "crypto";

function generateApiKey(): string {
  return randomBytes(16).toString("hex");
}

export { generateApiKey };
