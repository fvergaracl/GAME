import express from "express";
import { PointsController } from "../controllers/PointsController";

const router = express.Router();

/**
 * @swagger
 * /points/{userId}:
 *   get:
 *     tags: [Points]
 *     summary: Retrieve the total points of a user within a specified time range
 *     description: >
 *       This endpoint retrieves the total points accumulated by a user across all games and tasks,
 *       optionally within a specified time range. It requires the user ID, and optionally 'from' and 'to'
 *       date parameters, checks if the user exists, and sums up all the points assigned to the user.
 *     parameters:
 *       - in: path
 *         name: userId
 *         required: true
 *         schema:
 *           type: string
 *         description: ID of the user whose total points are to be retrieved.
 *       - in: query
 *         name: from
 *         required: false
 *         schema:
 *           type: string
 *           format: date-time
 *           example: 2023-11-23T00:00:00Z
 *         description: Start date to filter the points calculation. Should be in ISO format.
 *       - in: query
 *         name: to
 *         required: false
 *         schema:
 *           type: string
 *           format: date-time
 *           example: 2023-12-31T23:59:59Z
 *         description: End date to filter the points calculation. Should be in ISO format.
 *     responses:
 *       200:
 *         description: Total sum of points successfully retrieved
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 message:
 *                   type: string
 *                 points:
 *                   type: number
 *                   description: Total points accumulated by the user.
 *       400:
 *         description: User ID is required, or 'from'/'to' date parameters are invalid
 *       404:
 *         description: User not found, or user doesn't have actions/points
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 message:
 *                   type: string
 *                 points:
 *                   type: number
 *       500:
 *         description: Internal server error
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 message:
 *                   type: string
 *                 points:
 *                   type: number
 */
router.get("/:userId", PointsController.getUserPoints);

/**
 * @swagger
 * /points/{userId}/task/{idTask}:
 *   get:
 *     tags: [Points]
 *     summary: Retrieve the total points of a user for a specific task
 *     description: >
 *       This endpoint retrieves the total points accumulated by a user for a specific task.
 *       It requires both user ID and task ID, checks if the user exists, and sums up
 *       the points assigned for that task.
 *     parameters:
 *       - in: path
 *         name: userId
 *         required: true
 *         schema:
 *           type: string
 *         description: ID of the user whose points for the task are to be retrieved.
 *       - in: path
 *         name: idTask
 *         required: true
 *         schema:
 *           type: string
 *         description: ID of the task for which points are being retrieved.
 *     responses:
 *       200:
 *         description: Sum of points for the task successfully retrieved
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 message:
 *                   type: string
 *                 points:
 *                   type: number
 *                   description: Total points accumulated by the user for the task.
 *       400:
 *         description: User ID is required but was not provided
 *       404:
 *         description: User or task not found, or user doesn't have actions/points for this task
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 message:
 *                   type: string
 *                 points:
 *                   type: number
 *       500:
 *         description: Internal server error
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 message:
 *                   type: string
 *                 points:
 *                   type: number
 */
router.get("/:userId/task/:idTask", PointsController.getUserPointsInTask);

/**
 * @swagger
 * /points/{userId}/game/{idGame}:
 *   get:
 *     tags: [Points]
 *     summary: Retrieve the total points of a user in a specific game
 *     description: >
 *       This endpoint retrieves the total points accumulated by a user in a specified game.
 *       It requires both user ID and game ID, checks if the user exists, and calculates
 *       the sum of points assigned in the game.
 *     parameters:
 *       - in: path
 *         name: userId
 *         required: true
 *         schema:
 *           type: string
 *         description: ID of the user whose points are to be retrieved.
 *       - in: path
 *         name: idGame
 *         required: true
 *         schema:
 *           type: string
 *         description: ID of the game for which points are being retrieved.
 *     responses:
 *       200:
 *         description: Sum of points in the game successfully retrieved
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 message:
 *                   type: string
 *                 points:
 *                   type: number
 *                   description: Total points accumulated by the user in the game.
 *       400:
 *         description: User ID is required but was not provided
 *       404:
 *         description: User or game not found, or user doesn't have actions/points in this game
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 message:
 *                   type: string
 *                 points:
 *                   type: number
 *       500:
 *         description: Internal server error
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 message:
 *                   type: string
 *                 points:
 *                   type: number
 */
router.get("/:userId/game/:idGame", PointsController.getUserPointsInGame);

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
 *       201:
 *         description: Points successfully assigned to the user
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 message:
 *                   type: string
 *                   description: Success message.
 *                 points:
 *                   type: number
 *                   description: Points assigned to the user.
 *                 formula:
 *                   type: string
 *                   description: The formula used to calculate the points.
 *                 userIsCreated:
 *                   type: boolean
 *                   description: Indicates if a new user was created during the process.
 *       400:
 *         description: User ID is required but was not provided or points isn't calculated(because formula's strategy is not valid)
 *       404:
 *         description: Game, Task, or Strategy not found
 *       500:
 *         description: Internal server error
 */
router.post("/:idGame", PointsController.assignPointsToUser);

/**
 * @swagger
 * /points/{idGame}/{idTask}:
 *   post:
 *     tags: [Points]
 *     summary: Assign points to a user for a specific task within a game
 *     description: >
 *       This endpoint assigns points to a user based on their actions, the task performed,
 *       and the strategy parameters of a specified game. It validates the user, game, task,
 *       and performs complex calculations for point assignment.
 *     parameters:
 *       - in: path
 *         name: idGame
 *         required: true
 *         schema:
 *           type: string
 *         description: ID of the game related to the task.
 *       - in: path
 *         name: idTask
 *         required: true
 *         schema:
 *           type: string
 *         description: ID of the task for which points are being assigned.
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
 *       201:
 *         description: Points successfully assigned to the user
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 message:
 *                   type: string
 *                   description: Success message.
 *                 points:
 *                   type: number
 *                   description: Points assigned to the user.
 *                 formula:
 *                   type: string
 *                   description: The formula used to calculate the points.
 *                 userIsCreated:
 *                   type: boolean
 *                   description: Indicates if a new user was created during the process.
 *       400:
 *         description: User ID is required but was not provided or points isn't calculated(because formula's strategy is not valid)
 *       404:
 *         description: Game, Task, or Strategy not found or Task is not part of the Game
 *       500:
 *         description: Internal server error
 */
router.post("/:idGame/:idTask", PointsController.assignPointsToUser);

export default router;
