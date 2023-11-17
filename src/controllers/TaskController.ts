import { Request, Response } from "express";
import { TaskModel } from "../models";

class TaskController {
  static async getUserTasks(req: Request, res: Response) {
    try {
      const userId = req.params.id_user;
      const tasks = await TaskModel.find({ idUser: userId });
      res.json(tasks);
    } catch (error) {
      res.status(500).send(error);
    }
  }
}

export { TaskController };
