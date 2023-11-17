import express from "express";
import bodyParser from "body-parser";
import swaggerJsdoc from "swagger-jsdoc";
import indexRoute from "./routes/index";
import { options } from "./swaggerOptions";
import swaggerUi from "swagger-ui-express";

export const app = express();

const swaggerSpec = swaggerJsdoc(options);

// Middleware
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

app.use("/api-docs", swaggerUi.serve, swaggerUi.setup(swaggerSpec));

// Routes
app.use("/api/", indexRoute);

// Catch 404 and forward to error handler
app.use((req, res, next) => {
  const err = new Error("Not Found");
  res.status(404).json({ message: err.message });
});
/**
 * @swagger
 * /users:
 *   get:
 *     summary: Returns a list of users.
 *     responses:
 *       200:
 *         description: A list of users.
 *         content:
 *           application/json:
 *             schema:
 *               type: array
 *               items:
 *                 type: object
 *                 properties:
 *                   name:
 *                     type: string
 *                   email:
 *                     type: string
 */
app.use("/", (req, res) => {
  res.status(200).json({ message: "Welcome to the API" });
});

// Error handler
app.use(
  (
    err: any,
    req: express.Request,
    res: express.Response,
    next: express.NextFunction
  ) => {
    res.status(err.status || 500);
    res.json({
      error: {
        message: err.message,
      },
    });
  }
);
