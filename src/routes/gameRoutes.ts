import express from "express";
import { GameController } from "../controllers/GameController";

const router = express.Router();

/**
 * @swagger
 * /games:
 *   get:
 *     tags: [Games]
 *     summary: Retrieve a list of all games.
 *     responses:
 *       200:
 *         description: A list of games.
 *         content:
 *           application/json:
 *             schema:
 *               type: array
 *               items:
 *                 $ref: '#/components/schemas/Game'
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
 *             $ref: '#/components/schemas/Game'
 *     responses:
 *       201:
 *         description: New game created successfully.
 *       400:
 *         description: Invalid input data.
 */
router.post("/", GameController.createGame);

/**
 * @swagger
 * /games/{gameId}:
 *   put:
 *     tags: [Games]
 *     summary: Update an existing game.
 *     parameters:
 *       - in: path
 *         name: gameId
 *         required: true
 *         description: Unique ID of the game to be updated.
 *         schema:
 *           type: string
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             $ref: '#/components/schemas/Game'
 *     responses:
 *       200:
 *         description: Game updated successfully.
 *       404:
 *         description: Game not found.
 *       400:
 *         description: Invalid input data.
 */
router.put("/:gameId", GameController.updateGame);

/**
 * @swagger
 * /games/{gameId}:
 *   delete:
 *     tags: [Games]
 *     summary: Delete a game.
 *     parameters:
 *       - in: path
 *         name: gameId
 *         required: true
 *         description: Unique ID of the game to be deleted.
 *         schema:
 *           type: string
 *     responses:
 *       200:
 *         description: Game deleted successfully.
 *       404:
 *         description: Game not found.
 */
router.delete("/:gameId", GameController.deleteGame);

export default router;
