import { Request, Response } from "express";
import { TaskModel } from "../models";

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

  // Method to create a new task
  static async createTask(req: Request, res: Response) {
    try {
      const newTask = new TaskModel(req.body); // Assuming task details are sent in request body
      await newTask.save();
      res.status(201).json(newTask);
    } catch (error) {
      res.status(500).send(error);
    }
  }
}

export { TaskController };
