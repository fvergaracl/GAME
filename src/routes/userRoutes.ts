import express from "express";
import { UserController } from "../controllers/UserController";

const router = express.Router();

/**
 * @swagger
 * /users/{id}:
 *   get:
 *     tags: [Users]
 *     summary: Returns a specific user by ID.
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         description: Unique ID of the user.
 *         schema:
 *           type: string
 *     responses:
 *       200:
 *         description: A single user object.
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 userId:
 *                   type: string
 *                 games:
 *                   type: array
 *                   items:
 *                     type: object
 *                     properties:
 *                       gameId:
 *                         type: string
 *                       points:
 *                         type: number
 *                       strategyUsed:
 *                         type: string
 *       404:
 *         description: User not found.
 */

router.get("/:id", UserController.getUserById);

export default router;
