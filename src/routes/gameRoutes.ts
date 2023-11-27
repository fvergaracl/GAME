import express from "express";
import { GameController } from "../controllers/GameController";

const router = express.Router();

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
 *               - gameId
 *               - currentStrategyId
 *               - startDateTime
 *             properties:
 *               gameId:
 *                 type: string
 *                 description: Unique identifier for the game.
 *                 example: "Game123"
 *               currentStrategyId:
 *                 type: string
 *                 description: Unique identifier of the strategy associated with the game.
 *                 example: "5cc63cee-93e7-4007-9129-75deaaaa89f3"
 *               startDateTime:
 *                 type: string
 *                 format: date-time
 *                 description: Start date and time of the game.
 *                 example: "2023-01-01T00:00:00Z"
 *               endDateTime:
 *                 type: string
 *                 format: date-time
 *                 description: End date and time of the game (optional).
 *                 example: "2023-12-31T23:59:59Z"
 *               description:
 *                 type: string
 *                 description: Brief description of the game (optional).
 *                 example: "This is a strategy game focusing on individual and team challenges."
 *     responses:
 *       201:
 *         description: Game created successfully. Returns the details of the new game.
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Game'
 *       400:
 *         description: >
 *           Invalid input data. Possible reasons: missing required fields (gameId, currentStrategyId, startDateTime),
 *           game ID already exists, or strategy not found.
 *       500:
 *         description: Internal server error. Error details are not exposed to the client.
 */
router.post("/", GameController.createGame);

/**
 * @swagger
 * /games:
 *   get:
 *     tags: [Games]
 *     summary: Retrieve all games.
 *     responses:
 *       200:
 *         description: A list of games, each with their associated strategy.
 *         content:
 *           application/json:
 *             schema:
 *               type: array
 *               items:
 *                 $ref: '#/components/schemas/GameWithStrategy'
 *       500:
 *         description: Internal server error.
 *
 * components:
 *   schemas:
 *     GameWithStrategy:
 *       type: object
 *       properties:
 *         id:
 *           type: string
 *           format: uuid
 *           description: Unique identifier for the game.
 *         gameId:
 *           type: string
 *           description: Identifier for the game.
 *         startDateTime:
 *           type: string
 *           format: date-time
 *           description: Start date and time of the game.
 *         endDateTime:
 *           type: string
 *           format: date-time
 *           description: End date and time of the game (optional).
 *         description:
 *           type: string
 *           description: Brief description of the game (optional).
 *         currentStrategyId:
 *           type: string
 *           description: Unique identifier of the strategy associated with the game.
 *         strategy:
 *           $ref: '#/components/schemas/Strategy'
 */
router.get("/", GameController.getAllGames);

/**
 * @swagger
 * /games/{gameId}:
 *   get:
 *     tags: [Games]
 *     summary: Retrieve a specific game by its ID (gameId).
 *     parameters:
 *       - in: path
 *         name: gameId
 *         required: true
 *         description: Unique ID of the game.
 *         schema:
 *           type: string
 *     responses:
 *       200:
 *         description: Details of the specified game, including its associated strategy.
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/GameWithStrategy'
 *       400:
 *         description: Game ID is required.
 *       404:
 *         description: Game not found.
 *       500:
 *         description: Internal server error.
 *
 * components:
 *   schemas:
 *     GameWithStrategy:
 *       type: object
 *       properties:
 *         id:
 *           type: string
 *           format: uuid
 *           description: Unique identifier for the game.
 *         gameId:
 *           type: string
 *           description: Identifier for the game.
 *         startDateTime:
 *           type: string
 *           format: date-time
 *           description: Start date and time of the game.
 *         endDateTime:
 *           type: string
 *           format: date-time
 *           description: End date and time of the game (optional).
 *         description:
 *           type: string
 *           description: Brief description of the game (optional).
 *         currentStrategyId:
 *           type: string
 *           description: Unique identifier of the strategy associated with the game.
 *         strategy:
 *           $ref: '#/components/schemas/Strategy'
 */
router.get("/:gameId", GameController.getGameByGameId);

export default router;
