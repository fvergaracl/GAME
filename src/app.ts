import express from "express";
import bodyParser from "body-parser";
// Import routes
import indexRoute from "./routes/index";

export const app = express();

// Middleware
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Routes
app.use("/api/", indexRoute);

// Catch 404 and forward to error handler
app.use((req, res, next) => {
  const err = new Error("Not Found");
  res.status(404).json({ message: err.message });
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
