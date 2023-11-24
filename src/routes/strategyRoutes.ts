import express from "express";
import { StrategyController } from "../controllers/StrategyController";

const router = express.Router();

// /**
//  * @swagger
//  * /strategies:
//  *   get:
//  *     tags: [Strategies]
//  *     summary: Retrieve a list of all strategies.
//  *     responses:
//  *       200:
//  *         description: A list of strategies.
//  *         content:
//  *           application/json:
//  *             schema:
//  *               type: array
//  *               items:
//  *                 $ref: '#/components/schemas/Strategy'
//  */

// router.get("/", StrategyController.listAllStrategies);

// /**
//  * @swagger
//  * /strategies/{strategyId}:
//  *   get:
//  *     tags: [Strategies]
//  *     summary: Retrieve a specific strategy by its ID.
//  *     parameters:
//  *       - in: path
//  *         name: strategyId
//  *         required: true
//  *         description: Unique ID of the strategy.
//  *         schema:
//  *           type: string
//  *     responses:
//  *       200:
//  *         description: Details of the specified strategy.
//  *         content:
//  *           application/json:
//  *             schema:
//  *               $ref: '#/components/schemas/Strategy'
//  *       404:
//  *         description: Strategy not found.
//  */
// router.get("/:strategyId", StrategyController.getStrategyById);

/**
 * @swagger
 * /strategies:
 *   post:
 *     tags: [Strategies]
 *     summary: Create a new strategy.
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - name
 *               - description
 *               - strategyType
 *               - parameters
 *             properties:
 *               name:
 *                 type: string
 *                 default: "StandardGamificationStrategy"
 *               description:
 *                 type: string
 *                 default: "Strategy to calculate points based on individual and global behavior."
 *               strategyType:
 *                 type: string
 *                 default: "BehaviorBasedPoints"
 *               parameters:
 *                 type: object
 *                 default:
 *                   BASIC_POINTS: 10
 *                   BONUS_FACTOR: 1.5
 *                   SMALLER_BONUS: 0.5
 *                   INDIVIDUAL_IMPROVEMENT_FACTOR: 1.5
 *                   WEIGHT_GLOBAL_IMPROVE: 0.5
 *                   WEIGHT_INDIVIDUAL_IMPROVE: 0.5
 *               cases:
 *                 type: array
 *                 items:
 *                   type: object
 *                   required:
 *                     - criteria
 *                     - formula
 *                   properties:
 *                     criteria:
 *                       type: string
 *                     formula:
 *                       type: string
 *
 *     responses:
 *       201:
 *         description: New strategy created successfully.
 *       400:
 *         description: Invalid input data.
 */

router.post("/", StrategyController.createStrategy);

// /**
//  * @swagger
//  * /strategies/game/{gameId}:
//  *   get:
//  *     tags: [Strategies]
//  *     summary: Retrieve the strategy associated with a specific game.
//  *     parameters:
//  *       - in: path
//  *         name: gameId
//  *         required: true
//  *         description: Unique ID of the game.
//  *         schema:
//  *           type: string
//  *     responses:
//  *       200:
//  *         description: Strategy details for the specified game.
//  *         content:
//  *           application/json:
//  *             schema:
//  *               $ref: '#/components/schemas/Strategy'
//  *       404:
//  *         description: Game or strategy not found.
//  */
// router.get("/game/:gameId", StrategyController.getStrategyForGame);

export default router;
