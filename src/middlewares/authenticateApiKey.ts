import { Request, Response, NextFunction } from "express";
import { getToolByApiKey } from "../services/index";

interface AuthenticatedRequest extends Request {
  tool?: any;
}

const authenticateApiKey = async (
  req: AuthenticatedRequest,
  res: Response,
  next: NextFunction
) => {
  const apiKey = req.header("X-API-KEY");

  if (!apiKey) {
    return res.status(401).json({ error: "API key is required" });
  }

  const tool = await getToolByApiKey(apiKey); // Implementa esta función según tu base de datos

  if (!tool) {
    return res.status(403).json({ error: "Invalid API key" });
  }

  req.tool = tool; // Opcional: adjunta la información del usuario a la solicitud
  next();
};

export { authenticateApiKey };
