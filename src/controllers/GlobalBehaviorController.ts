import { Request, Response } from "express";
import { TaskModel } from "../models";

interface UserTaskTimes {
  [userId: string]: Date[];
}

class GlobalBehaviorController {
  static async calculateGlobalGameBehavior(req: Request, res: Response) {
    try {
      const { game_id } = req.params;
      const tasks = await TaskModel.find({ idGame: game_id }).sort("timestamp");

      const userTaskTimes = tasks.reduce((acc: UserTaskTimes, task) => {
        const userId = task.idUser.toString(); // Convert ObjectId to string
        acc[userId] = (acc[userId] || []).concat(task.timestamp);
        return acc;
      }, {});

      const averageTimes = Object.values(userTaskTimes)
        .filter((timestamps) => timestamps.length > 1)
        .map(GlobalBehaviorController.calculateAverageTime);

      const globalAverageTime = averageTimes.length
        ? averageTimes.reduce((a, b) => a + b, 0) / averageTimes.length
        : null;

      // count the number of tasks

      const tasksMeasured = tasks.length;

      res.json({ globalAverageTime, tasksMeasured });
    } catch (error) {
      res
        .status(500)
        .send({ message: "Error calculating global game behavior", error });
    }
  }

  static calculateAverageTime(timestamps: any[]) {
    return (
      timestamps.reduce((acc, time, index, arr) => {
        if (index === 0) return acc;
        return acc + (time - arr[index - 1]);
      }, 0) /
      (timestamps.length - 1)
    );
  }
}

export default GlobalBehaviorController;
