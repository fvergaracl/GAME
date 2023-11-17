import { MongoClient } from "mongodb";
import { dbConfig } from "./config";

const client = new MongoClient(dbConfig.uri);

export const connectDB = async () => {
  try {
    await client.connect();
    console.log("Conectado a la base de datos MongoDB");
  } catch (error) {
    console.error("No se pudo conectar a la base de datos MongoDB", error);
    process.exit(1);
  }
};
