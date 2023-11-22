import express from "express";
import { TaskController } from "../controllers/TaskController";

const router = express.Router();

// get All tasks getAllTasks

/**
 * @swagger
 * /tasks:
 *   get:
 *     tags: [Tasks]
 *     summary: Retrieve all tasks
 *     description: Fetches a list of all tasks from the database.
 *     responses:
 *       200:
 *         description: A list of tasks
 *         content:
 *           application/json:
 *             schema:
 *               type: array
 *               items:
 *                 $ref: '#/components/schemas/Task'
 *       500:
 *         description: Internal server error
 * components:
 *   schemas:
 *     Task:
 *       type: object
 *       properties:
 *         _id:
 *           type: string
 *           format: uuid
 *         name:
 *           type: string
 *         description:
 *           type: string
 *         idGame:
 *           type: string
 *           format: uuid
 *         game:
 *           $ref: '#/components/schemas/Game'
 *         createdBy:
 *           type: string
 *         createdAt:
 *           type: string
 *           format: date-time
 *     Game:
 *       type: object
 *       properties:
 *         _id:
 *           type: string
 *           format: uuid
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
 *         strategy:
 *           $ref: '#/components/schemas/Strategy'
 *         description:
 *           type: string
 *         createdBy:
 *           type: string
 *         createdAt:
 *           type: string
 *           format: date-time
 *     Strategy:
 *       type: object
 *       properties:
 *         name:
 *           type: string
 *         description:
 *           type: string
 *         strategyType:
 *           type: string
 *         parameters:
 *           $ref: '#/components/schemas/StrategyParameters'
 *         cases:
 *           type: array
 *           items:
 *             $ref: '#/components/schemas/Case'
 *     StrategyParameters:
 *       type: object
 *       properties:
 *         BASIC_POINTS:
 *           type: number
 *           description: Basic points assigned in the strategy.
 *         BONUS_FACTOR:
 *           type: number
 *           description: Factor applied to calculate bonus points. Optional.
 *         SMALLER_BONUS:
 *           type: number
 *           description: Smaller bonus value used in specific calculations. Optional.
 *         INDIVIDUAL_IMPROVEMENT_FACTOR:
 *           type: number
 *           description: Factor applied for individual improvements. Optional.
 *         WEIGHT_GLOBAL_IMPROVE:
 *           type: number
 *           description: Weight assigned to global improvement parameters. Optional.
 *         WEIGHT_INDIVIDUAL_IMPROVE:
 *           type: number
 *           description: Weight assigned to individual improvement parameters. Optional.
 *     Case:
 *       type: object
 *       properties:
 *         criteria:
 *           type: string
 *         formula:
 *           type: string
 *         subCases:
 *           type: object
 *           additionalProperties:
 *             $ref: '#/components/schemas/CaseSub'
 *     CaseSub:
 *       type: object
 *       properties:
 *         criteria:
 *           type: string
 *         formula:
 *           type: string
 */

router.get("/", TaskController.getAllTasks);

/**
 * @swagger
 * /tasks/{taskId}:
 *   get:
 *     tags: [Tasks]
 *     summary: Retrieve a task by its ID
 *     description: Fetches a task from the database based on the provided task ID.
 *     parameters:
 *       - in: path
 *         name: taskId
 *         required: true
 *         schema:
 *           type: string
 *         description: The ID of the task to retrieve
 *     responses:
 *       200:
 *         description: Details of the task with the specified ID
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Task'
 *       404:
 *         description: Task not found
 *       500:
 *         description: Internal server error
 * components:
 *   schemas:
 *     Task:
 *       type: object
 *       properties:
 *         _id:
 *           type: string
 *           format: uuid
 *         name:
 *           type: string
 *         description:
 *           type: string
 *         idGame:
 *           type: string
 *           format: uuid
 *         game:
 *           $ref: '#/components/schemas/Game'
 *         createdBy:
 *           type: string
 *         createdAt:
 *           type: string
 *           format: date-time
 *     Game:
 *       type: object
 *       properties:
 *         _id:
 *           type: string
 *           format: uuid
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
 *         strategy:
 *           $ref: '#/components/schemas/Strategy'
 *         description:
 *           type: string
 *         createdBy:
 *           type: string
 *         createdAt:
 *           type: string
 *           format: date-time
 *     Strategy:
 *       type: object
 *       properties:
 *         name:
 *           type: string
 *         description:
 *           type: string
 *         strategyType:
 *           type: string
 *         parameters:
 *           $ref: '#/components/schemas/StrategyParameters'
 *         cases:
 *           type: array
 *           items:
 *             $ref: '#/components/schemas/Case'
 *     StrategyParameters:
 *       type: object
 *       properties:
 *         BASIC_POINTS:
 *           type: number
 *           description: Basic points assigned in the strategy.
 *         BONUS_FACTOR:
 *           type: number
 *           description: Factor applied to calculate bonus points. Optional.
 *         SMALLER_BONUS:
 *           type: number
 *           description: Smaller bonus value used in specific calculations. Optional.
 *         INDIVIDUAL_IMPROVEMENT_FACTOR:
 *           type: number
 *           description: Factor applied for individual improvements. Optional.
 *         WEIGHT_GLOBAL_IMPROVE:
 *           type: number
 *           description: Weight assigned to global improvement parameters. Optional.
 *         WEIGHT_INDIVIDUAL_IMPROVE:
 *           type: number
 *           description: Weight assigned to individual improvement parameters. Optional.
 *     Case:
 *       type: object
 *       properties:
 *         criteria:
 *           type: string
 *         formula:
 *           type: string
 *         subCases:
 *           type: object
 *           additionalProperties:
 *             $ref: '#/components/schemas/CaseSub'
 *     CaseSub:
 *       type: object
 *       properties:
 *         criteria:
 *           type: string
 *         formula:
 *           type: string
 */
router.get("/:taskId", TaskController.getTaskById);

/**
 * @swagger
 * /tasks:
 *   post:
 *     tags: [Tasks]
 *     summary: Create a new task
 *     description: This endpoint creates a new task, optionally linked to a game.
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               name:
 *                 type: string
 *                 description: Name of the task.
 *                 example: Task example
 *               description:
 *                 type: string
 *                 description: Description of the task.
 *               idGame:
 *                 type: string
 *                 format: uuid
 *                 description: ID of the game associated with the task, if any.
 *                 example: 655ca7703c92c3582c7f5b4b
 *               createdBy:
 *                 type: string
 *                 description: ID of the user creating the task.
 *                 example: creatorName
 *             required:
 *               - name
 *               - createdBy
 *     responses:
 *       201:
 *         description: Successfully created task
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Task'
 *       404:
 *         description: Game not found (if idGame is provided)
 *       500:
 *         description: Internal server error
 * components:
 *   schemas:
 *     Task:
 *       type: object
 *       properties:
 *         _id:
 *           type: string
 *           format: uuid
 *         name:
 *           type: string
 *         description:
 *           type: string
 *         idGame:
 *           type: string
 *           format: uuid
 *         game:
 *           $ref: '#/components/schemas/Game'
 *         createdBy:
 *           type: string
 *         createdAt:
 *           type: string
 *           format: date-time
 *     Game:
 *       type: object
 *       properties:
 *         _id:
 *           type: string
 *           format: uuid
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
 *         strategy:
 *           $ref: '#/components/schemas/Strategy'
 *         description:
 *           type: string
 *         createdBy:
 *           type: string
 *         createdAt:
 *           type: string
 *           format: date-time
 */
router.post("/", TaskController.createTask);

export default router;
