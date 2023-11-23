import { app } from "./app";
import { initDefaultApiKeys } from "./services";
import { initDefaultStrategy } from "./services/initDefaultStrategy";
import connectDB from "./database";
import * as dotenv from "dotenv";

dotenv.config();

const PORT = process.env["PORT"] || 3000;

connectDB()
  .then(async () => {
    try {
      app.listen(PORT, () => console.log(`Server listening on port ${PORT}`));
    } catch (error) {
      console.error("Error during API key initialization:", error);
    }
  })
  .catch((error) => {
    console.error("Failed to connect to MongoDB:", error);
  })
  .then(async () => {
    try {
      await initDefaultApiKeys();
      await initDefaultStrategy();
    } catch (error) {
      console.error("Error during API key initialization:", error);
    }
  });
