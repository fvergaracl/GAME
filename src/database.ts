import { Sequelize, Dialect } from "sequelize";
import * as dotenv from "dotenv";
dotenv.config();

const sequelize = new Sequelize(
  process.env["DB_NAME"] || "postgres",
  process.env["DB_USER"] || "postgres",
  process.env["DB_PASSWORD"] || "",
  {
    host: process.env["DB_HOST"] || "localhost",
    port: parseInt(process.env["DB_PORT"] || "5432"),
    dialect: (process.env["DB_DIALECT"] as Dialect) || "postgres",
  }
);

export default sequelize;
