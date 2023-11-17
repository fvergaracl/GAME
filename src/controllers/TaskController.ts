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

  // Method to update an existing task
  static async updateTask(req: Request, res: Response) {
    try {
      const taskId = req.params.taskId;
      const updatedTask = await TaskModel.findByIdAndUpdate(taskId, req.body, {
        new: true,
      });
      if (!updatedTask) {
        return res.status(404).json({ message: "Task not found" });
      }
      res.json(updatedTask);
    } catch (error) {
      res.status(500).send(error);
    }
  }

  // Method to delete a task
  static async deleteTask(req: Request, res: Response) {
    try {
      const taskId = req.params.taskId;
      const deletedTask = await TaskModel.findByIdAndDelete(taskId);
      if (!deletedTask) {
        return res.status(404).json({ message: "Task not found" });
      }
      res.status(200).json({ message: "Task deleted successfully" });
    } catch (error) {
      res.status(500).send(error);
    }
  }
}

export { TaskController };
