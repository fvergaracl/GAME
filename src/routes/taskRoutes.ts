import express from "express";
import { TaskController } from "../controllers/TaskController";

const router = express.Router();

/**
 * @swagger
 * /tasks/user/{userId}:
 *   get:
 *     tags: [Tasks]
 *     summary: Returns tasks for a specific user.
 *     parameters:
 *       - in: path
 *         name: userId
 *         required: true
 *         description: Unique ID of the user to retrieve tasks for.
 *         schema:
 *           type: string
 *     responses:
 *       200:
 *         description: A list of tasks for the specified user.
 *         content:
 *           application/json:
 *             schema:
 *               type: array
 *               items:
 *                 type: object
 *                 properties:
 *                   timestamp:
 *                     type: string
 *                     format: date-time
 *                   idUser:
 *                     type: string
 *                   idGame:
 *                     type: string
 */
router.get("/user/:userId", TaskController.getUserTasks);

/**
 * @swagger
 * /tasks:
 *   post:
 *     tags: [Tasks]
 *     summary: Create a new task.
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - idUser
 *               - idGame
 *             properties:
 *               idUser:
 *                 type: string
 *                 description: ID of the user to whom the task belongs.
 *               idGame:
 *                 type: string
 *                 description: ID of the game associated with the task.
 *               timestamp:
 *                 type: string
 *                 format: date-time
 *                 description: Timestamp when the task is created or to be performed.
 *     responses:
 *       201:
 *         description: New task created successfully.
 *       400:
 *         description: Invalid input data.
 */
router.post("/", TaskController.createTask);

/**
 * @swagger
 * /tasks/{taskId}:
 *   put:
 *     tags: [Tasks]
 *     summary: Update an existing task.
 *     parameters:
 *       - in: path
 *         name: taskId
 *         required: true
 *         description: Unique ID of the task to be updated.
 *         schema:
 *           type: string
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               idUser:
 *                 type: string
 *                 description: ID of the user to whom the task belongs.
 *               idGame:
 *                 type: string
 *                 description: ID of the game associated with the task.
 *               timestamp:
 *                 type: string
 *                 format: date-time
 *                 description: Updated timestamp for the task.
 *     responses:
 *       200:
 *         description: Task updated successfully.
 *       404:
 *         description: Task not found.
 *       400:
 *         description: Invalid input data.
 */

router.put("/:taskId", TaskController.updateTask);

/**
 * @swagger
 * /tasks/{taskId}:
 *   delete:
 *     tags: [Tasks]
 *     summary: Delete a task.
 *     parameters:
 *       - in: path
 *         name: taskId
 *         required: true
 *         description: Unique ID of the task to be deleted.
 *         schema:
 *           type: string
 *     responses:
 *       200:
 *         description: Task deleted successfully.
 *       404:
 *         description: Task not found.
 */
router.delete("/:taskId", TaskController.deleteTask);

export default router;
