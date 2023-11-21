import express from "express";
import { PointsController } from "../controllers/PointsController";

const router = express.Router();
// GET points/:userId (all points for a user)
// GET points/:userId/:taskId (points for a user in a task)
// GET points/:userId/:gameId (all points for a user in a game)
// POST points/:userId/:taskId (create points for a user in a task)

router.get("/:userId", PointsController.getUserPoints);
router.get("/:userId/:taskId", PointsController.getUserPointsInTask);
router.get("/:userId/:gameId", PointsController.getUserPointsInGame);
router.post("/:userId/:taskId", PointsController.assignPointsToUser);


export default router;
