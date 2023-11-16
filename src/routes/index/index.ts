import { Router, Request, Response } from "express";
import dotenv from "dotenv";
import { authenticateApiKey } from "../../middlewares";
dotenv.config();

const router = Router();

router.get("/", (req: Request, res: Response) => {
  // version from package.json
  const { version } = require("../../../package.json");
  res.status(200).json({ message: "Hello World!", version });
});

// /testApiKey

export default router;
