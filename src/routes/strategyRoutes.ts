import express from "express";
import { StrategyController } from "../controllers/StrategyController";

const router = express.Router();

/**
 * @swagger
 * /strategies:
 *   get:
 *     tags: [Strategies]
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
 */

router.get("/", StrategyController.listAllStrategies);

/**
 * @swagger
 * /strategies/{strategyId}:
 *   get:
 *     tags: [Strategies]
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
 */
router.get("/:strategyId", StrategyController.getStrategyById);

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
 *               description:
 *                 type: string
 *               strategyType:
 *                 type: string
 *               parameters:
 *                 type: object
 *                 properties:
 *                   defaultPointsTaskCampaign:
 *                     type: number
 *                   weightIndividualImprove:
 *                     type: number
 *                   weightGlobalImprove:
 *                     type: number
 *                   minorBonus:
 *                     type: number
 *               cases:
 *                 type: object
 *                 additionalProperties:
 *                   type: object
 *                   properties:
 *                     description:
 *                       type: string
 *                     calculatePoints:
 *                       type: string
 *                     subCases:
 *                       type: object
 *                       additionalProperties:
 *                         type: object
 *                         properties:
 *                           condition:
 *                             type: string
 *                           calculatePoints:
 *                             type: string
 *     responses:
 *       201:
 *         description: New strategy created successfully.
 *       400:
 *         description: Invalid input data.
 *     examples:
 *       application/json:
 *         value: # Example value
 *           name: "StandardGamificationStrategy"
 *           description: "Strategy to calculate points based on individual and global behavior."
 *           strategyType: "BehaviorBasedPoints"
 *           parameters:
 *             defaultPointsTaskCampaign: 10
 *             weightIndividualImprove: 10
 *             weightGlobalImprove: 10
 *             minorBonus: 5
 *           cases:
 *             case1:
 *               description: "First or second task of the user without global behavior data."
 *               calculatePoints: "defaultPointsTaskCampaign"
 *             case2:
 *               description: "Second task of the user with available global behavior data."
 *               subCases:
 *                 "2.1":
 *                   condition: "timeInvestedLastTask > globalCalculation"
 *                   calculatePoints: "defaultPointsTaskCampaign"
 *                 "2.2":
 *                   condition: "timeInvestedLastTask < globalCalculation"
 *                   calculatePoints: "defaultPointsTaskCampaign + Bonus"
 *             case3:
 *               description: "Individual behavior data available, no global behavior."
 *               calculatePoints: "defaultPointsTaskCampaign"
 *             case4:
 *               description: "Complete individual and global behavior data."
 *               subCases:
 *                 "4.1":
 *                   condition: "timeInvestedLastTask < individualCalculation AND timeInvestedLastTask > globalCalculation"
 *                   calculatePoints: "FormulaBased"
 *                 "4.2":
 *                   condition: "timeInvestedLastTask > individualCalculation AND timeInvestedLastTask > globalCalculation"
 *                   calculatePoints: "defaultPointsTaskCampaign"
 *                 "4.3":
 *                   condition: "timeInvestedLastTask < individualCalculation AND timeInvestedLastTask < globalCalculation"
 *                   calculatePoints: "FormulaBasedMaxBonus"
 *                 "4.4":
 *                   condition: "timeInvestedLastTask > individualCalculation AND timeInvestedLastTask < globalCalculation"
 *                   calculatePoints: "defaultPointsTaskCampaign + MinorBonus"
 */

router.post("/", StrategyController.createStrategy);

/**
 * @swagger
 * /strategies/game/{gameId}:
 *   get:
 *     tags: [Strategies]
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

/**
 * @swagger
 * /strategies/copy/{strategyId}:
 *   post:
 *     tags: [Strategies]
 *     summary: Copy an existing strategy.
 *     parameters:
 *       - in: path
 *         name: strategyId
 *         required: true
 *         description: Unique ID of the strategy to be copied.
 *         schema:
 *           type: string
 *     requestBody:
 *       description: Optional modifications to apply to the copied strategy.
 *       required: false
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *     responses:
 *       201:
 *         description: Strategy copied successfully.
 *       404:
 *         description: Original strategy not found.
 *       400:
 *         description: Invalid input data.
 */
router.post("/copy/:strategyId", StrategyController.copyStrategy);

export default router;
