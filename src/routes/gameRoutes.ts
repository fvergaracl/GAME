import express from "express";
import { GameController } from "../controllers/GameController";

const router = express.Router();

/**
 * @swagger
 * components:
 *   schemas:
 *     Game:
 *       type: object
 *       required:
 *         - identification
 *         - timestampStart
 *         - currentStrategyId
 *         - createdBy
 *       properties:
 *         identification:
 *           type: string
 *         timestampEnd:
 *           type: string
 *           format: date-time
 *         timestampStart:
 *           type: string
 *           format: date-time
 *         currentStrategyId:
 *           type: string
 *           format: uuid
 *         description:
 *           type: string
 *         createdBy:
 *           type: string
 * /games:
 *   get:
 *     tags: [Games]
 *     summary: Retrieve a list of all games.
 *     responses:
 *       200:
 *         description: A list of games. Can be empty if no games are available.
 *         content:
 *           application/json:
 *             schema:
 *               type: array
 *               items:
 *                 $ref: '#/components/schemas/Game'
 *       500:
 *         description: Internal server error. Error details are not exposed to the client.
 */
router.get("/", GameController.getAllGames);

/**
 * @swagger
 * /games/{gameId}:
 *   get:
 *     tags: [Games]
 *     summary: Retrieve a specific game by its ID.
 *     parameters:
 *       - in: path
 *         name: gameId
 *         required: true
 *         description: Unique ID of the game.
 *         schema:
 *           type: string
 *     responses:
 *       200:
 *         description: Details of the specified game.
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Game'
 *       404:
 *         description: Game not found.
 */
router.get("/:gameId", GameController.getGameById);

/**
 * @swagger
 * /games:
 *   post:
 *     tags: [Games]
 *     summary: Create a new game.
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - identification
 *               - timestampStart
 *               - currentStrategy
 *               - defaultPointsTaskCampaign
 *               - createdBy
 *             properties:
 *               identification:
 *                 type: string
 *                 example: "Game123"
 *               timestampEnd:
 *                 type: string
 *                 format: date-time
 *                 example: "2023-12-31T23:59:59Z"
 *               timestampStart:
 *                 type: string
 *                 format: date-time
 *                 example: "2023-01-01T00:00:00Z"
 *               currentStrategyId:
 *                 type: string
 *                 example: "625f6f5e6b0915c7f4fbdc62"
 *               description:
 *                 type: string
 *                 example: "This is a strategy game focusing on individual and team challenges."
 *               createdBy:
 *                 type: string
 *                 example: "user123"
 *     responses:
 *       201:
 *         description: Game created successfully. Returns the ID of the new game.
 *       400:
 *         description: >
 *           Invalid input data. Possible reasons: missing fields (identification, timestamps, currentStrategyId, createdBy),
 *           invalid timestamps, end timestamp is before the start timestamp.
 *       404:
 *         description: Strategy not found. The provided currentStrategyId does not correspond to any existing strategy.
 *       500:
 *         description: Internal server error. Error details are not exposed to the client.
 */
router.post("/", GameController.createGame);

/*

router.delete("/:gameId", GameController.deleteGame);
*/

export default router;
