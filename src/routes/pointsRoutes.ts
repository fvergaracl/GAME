import express from "express";
import { PointsController } from "../controllers/PointsController";

const router = express.Router();

/**
 * @swagger
 * /points/assign:
 *   post:
 *     tags: [Points]
 *     summary: Assign points to a user for completing a task in a game.
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - userId
 *               - gameId
 *               - points
 *             properties:
 *               userId:
 *                 type: string
 *                 description: ID of the user to whom the points will be assigned.
 *               gameId:
 *                 type: string
 *                 description: ID of the game for which points are being assigned.
 *               points:
 *                 type: number
 *                 description: Number of points to be assigned.
 *     responses:
 *       200:
 *         description: Points successfully assigned to the user.
 *       400:
 *         description: Invalid input data.
 *       404:
 *         description: User or game not found.
 */
router.post("/assign", PointsController.assignPointsToUser);

export default router;
