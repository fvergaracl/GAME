import { Request, Response } from "express";
import { TaskModel } from "../models";

class IndividualBehaviorController {
  static async calculateIndividualGameBehavior(req: Request, res: Response) {
    try {
      const { id_user, game_id } = req.params;

      // Retrieve and sort tasks by timestamp
      const tasks = await TaskModel.find({
        idUser: id_user,
        idGame: game_id,
      }).sort("timestamp");
      const tasksMeasured = tasks.length;

      // Early return for insufficient tasks
      if (tasks.length < 2) {
        return res.json({ averageTime: null, tasksMeasured });
      }

      // Calculate the average time using array methods for cleaner code
      const totalTimeInterval = tasks.slice(1).reduce((acc, task, index) => {
        const prevTimestamp = tasks[index].timestamp.getTime();
        const currentTimestamp = task.timestamp.getTime();
        return acc + (currentTimestamp - prevTimestamp);
      }, 0);

      const averageTime = totalTimeInterval / (tasks.length - 1);

      res.json({ averageTime, tasksMeasured });
    } catch (error) {
      // Handle unexpected errors more gracefully
      console.error("Error calculating individual game behavior:", error);
      res
        .status(500)
        .send("An error occurred while calculating the game behavior.");
    }
  }
}

export default IndividualBehaviorController;
