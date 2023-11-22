import { Request, Response } from "express";
import { TaskModel, GameModel } from "../models";

class TaskController {
  // Method to retrieve tasks for a specific user
  static async getUserTasks(req: Request, res: Response) {
    try {
      const userId = req.params.id_user;
      const tasks = await TaskModel.find({ idUser: userId });
      res.json(tasks);
    } catch (error) {
      res.status(500).send(error);
    }
  }

  // get all tasks
  static async getAllTasks(_: Request, res: Response) {
    try {
      const tasks = await TaskModel.find({});
      res.status(200).json(tasks);
    } catch (error) {
      res.status(500).send(error);
    }
  }

  static async getTaskById(req: Request, res: Response) {
    try {
      const taskId = req.params.taskId;
      const task = await TaskModel.findById(taskId);
      if (!task) {
        return res.status(404).json({ message: "Task not found" });
      }
      res.status(200).json(task);
    } catch (error) {
      res.status(500).send(error);
    }
  }

  static async createTask(req: Request, res: Response) {
    try {
      const body = req.body;
      // Check if idGame exists
      let game = undefined;
      let newTask = {
        ...body,
        createdAt: new Date(),
      };
      if (body?.idGame) {
        game = await GameModel.findById(body.idGame);
        if (!game) {
          return res.status(404).json({ message: "Game not found" });
        }
      }
      if (game) {
        newTask = {
          ...newTask,
          game,
        };
      }
      const task = await TaskModel.create(newTask);
      res.status(201).json(task);
    } catch (error) {
      res.status(500).send(error);
    }
  }
}

export { TaskController };
