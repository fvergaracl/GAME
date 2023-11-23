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

/**
 * @swagger
 * /points/{idGame}:
 *   post:
 *     tags: [Points]
 *     summary: Assign points to a user for a game
 *     description: >
 *       This endpoint assigns points to a user based on their actions and
 *       the strategy parameters of a specified game. It handles user and game
 *       validation, task checks, and complex calculations for point assignment.
 *     parameters:
 *       - in: path
 *         name: idGame
 *         required: true
 *         schema:
 *           type: string
 *         description: ID of the game related to the task.
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               userId:
 *                 type: string
 *                 description: ID of the user to whom points are to be assigned.
 *     responses:
 *       200:
 *         description: Points successfully assigned to the user
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 message:
 *                   type: string
 *                 maxPoints:
 *                   type: number
 *                   description: Maximum points calculated for the user.
 *                 allClasses:
 *                   type: array
 *                   items:
 *                     type: object
 *                     properties:
 *                       # Define the structure for items in allClasses here
 *       404:
 *         description: Game or Task not found
 *       500:
 *         description: Internal server error
 */
router.post("/:idGame", PointsController.assignPointsToUser);

/**
 * @swagger
 * /points/:idGame/:idTask:
 *   post:
 *     tags: [Points]
 *     summary: Assign points to a user for a task within a game
 *     description: >
 *      This endpoint assigns points to a user based on their actions and
 *      the strategy parameters of a specified game. It handles user and game
 *      validation, task checks, and complex calculations for point assignment.
 *     parameters:
 *       - in: path
 *         name: idGame
 *         required: true
 *         schema:
 *           type: string
 *
 *         description: ID of the game related to the task.
 *       - in: path
 *         name: idTask
 *         required: true
 *         schema:
 *           type: string
 *         description: ID of the task related to the points.
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               userId:
 *                 type: string
 *                 description: ID of the user to whom points are to be assigned.
 *     responses:
 *       200:
 *         description: Points successfully assigned to the user
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 message:
 *                   type: string
 *                 maxPoints:
 *                   type: number
 *                   description: Maximum points calculated for the user.
 *                 allClasses:
 *                   type: array
 *                   items:
 *                     type: object
 *                     properties:
 *                       # Define the structure for items in allClasses here
 *       404:
 *         description: Game or Task not found
 *       500:
 *         description: Internal server error
 */
router.post("/:idGame/:idTask", PointsController.assignPointsToUser);

export default router;
