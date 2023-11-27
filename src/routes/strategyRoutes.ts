import express from "express";
import { StrategyController } from "../controllers/StrategyController";

const router = express.Router();

/**
 * @swagger
 * components:
 *   schemas:
 *     Strategy:
 *       type: object
 *       required:
 *         - name
 *         - description
 *         - strategyType
 *         - parameters
 *         - cases
 *       properties:
 *         id:
 *           type: string
 *           format: uuid
 *           description: Unique identifier for the strategy
 *         name:
 *           type: string
 *           description: Name of the strategy
 *         description:
 *           type: string
 *           description: Description of the strategy
 *         strategyType:
 *           type: string
 *           description: Type of the strategy
 *         parameters:
 *           type: object
 *           properties:
 *             BASIC_POINTS:
 *               type: integer
 *             BONUS_FACTOR:
 *               type: integer
 *             SMALLER_BONUS:
 *               type: integer
 *             INDIVIDUAL_IMPROVEMENT_FACTOR:
 *               type: integer
 *             WEIGHT_GLOBAL_IMPROVE:
 *               type: integer
 *             WEIGHT_INDIVIDUAL_IMPROVE:
 *               type: integer
 *           description: Parameters for the strategy
 *         cases:
 *           type: array
 *           items:
 *             type: object
 *             properties:
 *               criteria:
 *                 type: string
 *               formula:
 *                 type: string
 *               subCases:
 *                 type: array
 *                 items:
 *                   type: object
 *                   properties:
 *                     criteria:
 *                       type: string
 *                     formula:
 *                       type: string
 *             description: Cases for the strategy
 *       example:
 *         id: "5cc63cee-93e7-4007-9129-75deaaaa89f3"
 *         name: "StandardGamificationStrategy"
 *         description: "Strategy to calculate points based on individual and global behavior."
 *         strategyType: "BehaviorBasedPoints"
 *         parameters:
 *           BASIC_POINTS: 10
 *           BONUS_FACTOR: 1.5
 *           SMALLER_BONUS: 0.5
 *           INDIVIDUAL_IMPROVEMENT_FACTOR: 1.5
 *           WEIGHT_GLOBAL_IMPROVE: 0.5
 *           WEIGHT_INDIVIDUAL_IMPROVE: 0.5
 *         cases:
 *           - criteria: "EARLY_TASK_NO_GLOBAL"
 *             formula: "FORMULA_BASIC_POINTS"
 *           - criteria: "SECOND_TASK_GLOBAL_DATA"
 *             formula: "FORMULA_GLOBAL_AVERAGE_COMPARISON"
 *           - criteria: "INDIVIDUAL_DATA_NO_GLOBAL"
 *             formula: "FORMULA_USER_AVERAGE_COMPARISON"
 *           - criteria: "BOTH_INDIVIDUAL_GLOBAL_DATA"
 *             formula: "FORMULA_GLOBAL_AND_INDIVIDUAL_IMPROVEMENT"
 *
 * /strategies:
 *   get:
 *     tags:
 *       - Strategies
 *     summary: Retrieve a list of all strategies.
 *     responses:
 *       200:
 *         description: A list of strategies.
 *         content:
 *           application/json:
 *             schema:
 *               type: array
 *               items:
 *                 $ref: '#/components/schemas/Strategy'
 *       500:
 *         description: Internal server error.
 */
router.get("/", StrategyController.listAllStrategies);

/**
 * @swagger
 * components:
 *   schemas:
 *     Strategy:
 *       type: object
 *       required:
 *         - name
 *         - description
 *         - strategyType
 *         - parameters
 *         - cases
 *       properties:
 *         id:
 *           type: string
 *           format: uuid
 *           description: Unique identifier for the strategy
 *         name:
 *           type: string
 *           description: Name of the strategy
 *         description:
 *           type: string
 *           description: Description of the strategy
 *         strategyType:
 *           type: string
 *           description: Type of the strategy
 *         parameters:
 *           type: object
 *           properties:
 *             BASIC_POINTS:
 *               type: integer
 *             BONUS_FACTOR:
 *               type: integer
 *             SMALLER_BONUS:
 *               type: integer
 *             INDIVIDUAL_IMPROVEMENT_FACTOR:
 *               type: integer
 *             WEIGHT_GLOBAL_IMPROVE:
 *               type: integer
 *             WEIGHT_INDIVIDUAL_IMPROVE:
 *               type: integer
 *           description: Parameters for the strategy
 *         cases:
 *           type: array
 *           items:
 *             type: object
 *             properties:
 *               criteria:
 *                 type: string
 *               formula:
 *                 type: string
 *               subCases:
 *                 type: array
 *                 items:
 *                   type: object
 *                   properties:
 *                     criteria:
 *                       type: string
 *                     formula:
 *                       type: string
 *             description: Cases for the strategy
 *       example:
 *         id: "5cc63cee-93e7-4007-9129-75deaaaa89f3"
 *         name: "StandardGamificationStrategy"
 *         description: "Strategy to calculate points based on individual and global behavior."
 *         strategyType: "BehaviorBasedPoints"
 *         parameters:
 *           BASIC_POINTS: 10
 *           BONUS_FACTOR: 1.5
 *           SMALLER_BONUS: 0.5
 *           INDIVIDUAL_IMPROVEMENT_FACTOR: 1.5
 *           WEIGHT_GLOBAL_IMPROVE: 0.5
 *           WEIGHT_INDIVIDUAL_IMPROVE: 0.5
 *         cases:
 *           - criteria: "EARLY_TASK_NO_GLOBAL"
 *             formula: "FORMULA_BASIC_POINTS"
 *           - criteria: "SECOND_TASK_GLOBAL_DATA"
 *             formula: "FORMULA_GLOBAL_AVERAGE_COMPARISON"
 *           - criteria: "INDIVIDUAL_DATA_NO_GLOBAL"
 *             formula: "FORMULA_USER_AVERAGE_COMPARISON"
 *           - criteria: "BOTH_INDIVIDUAL_GLOBAL_DATA"
 *             formula: "FORMULA_GLOBAL_AND_INDIVIDUAL_IMPROVEMENT"
 *
 * /strategies/{strategyId}:
 *   get:
 *     tags:
 *       - Strategies
 *     summary: Retrieve a specific strategy by its ID.
 *     parameters:
 *       - in: path
 *         name: strategyId
 *         required: true
 *         description: Unique ID of the strategy.
 *         schema:
 *           type: string
 *     responses:
 *       200:
 *         description: Details of the specified strategy.
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Strategy'
 *       404:
 *         description: Strategy not found.
 *       500:
 *         description: Internal server error.
 */
router.get("/:strategyId", StrategyController.getStrategyById);

/**
 * @swagger
 * components:
 *   schemas:
 *     Strategy:
 *       type: object
 *       required:
 *         - name
 *         - description
 *         - strategyType
 *         - parameters
 *         - cases
 *       properties:
 *         id:
 *           type: string
 *           format: uuid
 *           description: Unique identifier for the strategy
 *         name:
 *           type: string
 *           description: Name of the strategy
 *         description:
 *           type: string
 *           description: Description of the strategy
 *         strategyType:
 *           type: string
 *           description: Type of the strategy
 *         parameters:
 *           type: object
 *           properties:
 *             BASIC_POINTS:
 *               type: integer
 *             BONUS_FACTOR:
 *               type: integer
 *             SMALLER_BONUS:
 *               type: integer
 *             INDIVIDUAL_IMPROVEMENT_FACTOR:
 *               type: integer
 *             WEIGHT_GLOBAL_IMPROVE:
 *               type: integer
 *             WEIGHT_INDIVIDUAL_IMPROVE:
 *               type: integer
 *           description: Parameters for the strategy
 *         cases:
 *           type: array
 *           items:
 *             type: object
 *             properties:
 *               criteria:
 *                 type: string
 *               formula:
 *                 type: string
 *               subCases:
 *                 type: array
 *                 items:
 *                   type: object
 *                   properties:
 *                     criteria:
 *                       type: string
 *                     formula:
 *                       type: string
 *             description: Cases for the strategy
 *       example:
 *         name: "StandardGamificationStrategy"
 *         description: "Strategy to calculate points based on individual and global behavior."
 *         strategyType: "BehaviorBasedPoints"
 *         parameters:
 *           BASIC_POINTS: 10
 *           BONUS_FACTOR: 1.5
 *           SMALLER_BONUS: 0.5
 *           INDIVIDUAL_IMPROVEMENT_FACTOR: 1.5
 *           WEIGHT_GLOBAL_IMPROVE: 0.5
 *           WEIGHT_INDIVIDUAL_IMPROVE: 0.5
 *         cases:
 *           - criteria: "EARLY_TASK_NO_GLOBAL"
 *             formula: "FORMULA_BASIC_POINTS"
 *           - criteria: "SECOND_TASK_GLOBAL_DATA"
 *             formula: "FORMULA_GLOBAL_AVERAGE_COMPARISON"
 *           - criteria: "INDIVIDUAL_DATA_NO_GLOBAL"
 *             formula: "FORMULA_USER_AVERAGE_COMPARISON"
 *           - criteria: "BOTH_INDIVIDUAL_GLOBAL_DATA"
 *             formula: "FORMULA_GLOBAL_AND_INDIVIDUAL_IMPROVEMENT"
 *
 * /strategies:
 *   post:
 *     tags:
 *       - Strategies
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
 *               - cases
 *             properties:
 *               name:
 *                 type: string
 *               description:
 *                 type: string
 *               strategyType:
 *                 type: string
 *               parameters:
 *                 type: object
 *                 properties:
 *                   BASIC_POINTS:
 *                     type: integer
 *                   BONUS_FACTOR:
 *                     type: integer
 *                   SMALLER_BONUS:
 *                     type: integer
 *                   INDIVIDUAL_IMPROVEMENT_FACTOR:
 *                     type: integer
 *                   WEIGHT_GLOBAL_IMPROVE:
 *                     type: integer
 *                   WEIGHT_INDIVIDUAL_IMPROVE:
 *                     type: integer
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
 *     responses:
 *       201:
 *         description: New strategy created successfully.
 *       400:
 *         description: Invalid input data.
 *       500:
 *         description: Internal server error.
 */
router.post("/", StrategyController.createStrategy);

/**
 * @swagger
 * components:
 *   schemas:
 *     Strategy:
 *       type: object
 *       required:
 *         - id
 *         - name
 *         - description
 *         - strategyType
 *         - parameters
 *         - cases
 *       properties:
 *         id:
 *           type: string
 *           format: uuid
 *           description: Unique identifier for the strategy.
 *         name:
 *           type: string
 *           description: Name of the strategy.
 *         description:
 *           type: string
 *           description: Description of the strategy.
 *         strategyType:
 *           type: string
 *           description: Type of the strategy.
 *         parameters:
 *           type: object
 *           additionalProperties:
 *             type: number
 *           description: Parameters for the strategy.
 *         cases:
 *           type: array
 *           items:
 *             type: object
 *             properties:
 *               criteria:
 *                 type: string
 *               formula:
 *                 type: string
 *               subCases:
 *                 type: array
 *                 items:
 *                   type: object
 *                   properties:
 *                     criteria:
 *                       type: string
 *                     formula:
 *                       type: string
 *
 * /strategies/game/{gameId}:
 *   get:
 *     tags:
 *       - Strategies
 *     summary: Retrieve the strategy associated with a specific game.
 *     parameters:
 *       - in: path
 *         name: gameId
 *         required: true
 *         description: Unique ID of the game.
 *         schema:
 *           type: string
 *     responses:
 *       200:
 *         description: Strategy details for the specified game.
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Strategy'
 *       404:
 *         description: Game or strategy not found.
 */
router.get("/game/:gameId", StrategyController.getStrategyForGame);

export default router;
