import express from "express";
import bodyParser from "body-parser";
import swaggerJsdoc from "swagger-jsdoc";
import indexRoute from "./routes/index";
import { options } from "./swaggerOptions";
import swaggerUi from "swagger-ui-express";

import gameRoutes from "./routes/gameRoutes";
// import pointsRoutes from "./routes/pointsRoutes";
import strategyRoutes from "./routes/strategyRoutes";
// import taskRoutes from "./routes/taskRoutes";
// import userRoutes from "./routes/userRoutes";

export const app = express();

const swaggerSpec = swaggerJsdoc(options);

// Middleware
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

app.use("/api-docs", swaggerUi.serve, swaggerUi.setup(swaggerSpec));

// Routes
app.use("/", indexRoute);
app.use("/api/", indexRoute);
// Routes
app.use("/games", gameRoutes);
// app.use("/points", pointsRoutes);
app.use("/strategies", strategyRoutes);
// app.use("/tasks", taskRoutes);
// app.use("/users", userRoutes);

// Catch 404 and forward to error handler
app.use((_, res, __) => {
  const err = new Error("Endpoint Not Found");
  res.status(404).json({ message: err.message });
});

// Error handler
app.use(
  (
    err: any,
    _: express.Request,
    res: express.Response,
    __: express.NextFunction
  ) => {
    res.status(err.status || 500);
    res.json({
      error: {
        message: err.message,
      },
    });
  }
);
