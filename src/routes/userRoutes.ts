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

/**
 * @swagger
 * /users:
 *   post:
 *     tags: [Users]
 *     summary: Creates a new user.
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               userId:
 *                 type: string
 *     responses:
 *       201:
 *         description: The created user object.
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
 *       400:
 *         description: User ID is required.
 */
router.post("/", UserController.createUser);

/**
 * @swagger
 * /users/{id}:
 *  put:
 *    tags: [Users]
 *    summary: Updates an existing user by ID.
 *    parameters:
 *      - in: path
 *        name: id
 *        required: true
 *        description: Unique ID of the user.
 *        schema:
 *          type: string
 *    requestBody:
 *      required: true
 *      content:
 *        application/json:
 *          schema:
 *            $ref: '#/definitions/User'
 *    responses:
 *      200:
 *        description: The updated user object.
 *        content:
 *          application/json:
 *            schema:
 *              $ref: '#/definitions/User'
 *      404:
 *        description: User not found.
 *      400:
 *        description: User ID is required.
 */
router.put("/:id", UserController.updateUser);

/**
 * @swagger
 * /users/{id}:
 *   delete:
 *     tags: [Users]
 *     summary: Deletes a user by ID.
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         description: Unique ID of the user.
 *         schema:
 *           type: string
 *     responses:
 *       200:
 *         description: User deleted successfully.
 *       404:
 *         description: User not found.
 */
router.delete("/:id", UserController.deleteUser);

export default router;
