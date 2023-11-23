import { Request, Response, NextFunction } from "express";
import { getToolByApiKey } from "../services/index";

interface AuthenticatedRequest extends Request {
  tool?: any; // Considera usar un tipo más específico que 'any' si es posible
}

const authenticateApiKey = async (
  req: AuthenticatedRequest,
  res: Response,
  next: NextFunction
): Promise<void> => { // Asegúrate de que la función devuelva Promise<void>
  const apiKey = req.header("X-API-KEY");

  if (!apiKey) {
    res.status(401).json({ error: "API key is required" });
    return; // Asegúrate de que la función termina aquí
  }

  const tool = await getToolByApiKey(apiKey); // Implementa esta función según tu base de datos

  if (!tool) {
    res.status(403).json({ error: "Invalid API key" });
    return; // Asegúrate de que la función termina aquí
  }

  req.tool = tool; // Opcional: adjunta la información del usuario a la solicitud
  next(); // Llama a next al final si todo está correcto
};

export { authenticateApiKey };
