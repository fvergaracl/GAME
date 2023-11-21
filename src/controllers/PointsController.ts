import { Request, Response } from "express";
import {
  PointsModel,
  TaskModel,
  Task,
  StrategyModel,
  Strategy,
  GameModel,
  UserModel,
  GlobalBehaviorModel,
} from "../models";

class PointsController {
  static async assignPointsToUser(req: Request, res: Response) {
    try {
      
    } catch (error) {
      
    }
    /*
    try {
      
      const { userId, gameId } = req.params;

      // Retrieve the game strategy
      const game = await GameModel.findById(gameId);
      if (!game) {
        return res.status(404).json({ message: "Game not found" });
      }
      const strategy = await StrategyModel.findById(game.currentStrategy);
      if (!strategy) {
        return res.status(404).json({ message: "Strategy not found" });
      }

      // Retrieve user's tasks and global behavior for the game
      const tasks = await TaskModel.find({
        idUser: userId,
        idGame: gameId,
      }).sort("timestamp");
      const globalBehavior = await GlobalBehaviorModel.findOne({
        gameId: gameId,
      });

      // Calculate individual behavior
      const individualAverageTime = calculateIndividualAverageTime(tasks);

      // Calculate points based on strategy
      let points = game.defaultPointsTaskCampaign; // Starting with default points
      if (individualAverageTime && globalBehavior) {
        points += calculateStrategyPoints(
          individualAverageTime,
          strategy,
          globalBehavior.averageTime,
          globalBehavior.previousAverageTime
        );
      }

      // Update or create points record
      const pointsRecord = await PointsModel.findOne({
        idUser: userId,
        idGame: gameId,
      });
      if (pointsRecord) {
        pointsRecord.points += points;
        await pointsRecord.save();
      }
      if (!pointsRecord) {
        const newPointsRecord = new PointsModel({
          idUser: userId,
          idGame: gameId,
          points: points,
          strategyUsed: game.currentStrategy,
        });
        await newPointsRecord.save();
      }

      // Update user's game points
      await UserModel.updateOne(
        { userId: userId, "games.gameId": gameId },
        { $inc: { "games.$.points": points } },
        { upsert: true }
      );

      res
        .status(200)
        .json({ message: "Points successfully assigned", points: points });
    } catch (error) {
      console.error(error);
      res.status(500).send(error);
    }
    */
  }
}

function calculateIndividualAverageTime(tasks: Task[]): number | null {
  if (tasks.length < 2) {
    // If there are fewer than two tasks, it's not possible to calculate an average time
    return null;
  }

  let totalTimeInterval = 0;
  for (let i = 1; i < tasks.length; i++) {
    const previousTaskTime = tasks[i - 1].timestamp.getTime();
    const currentTaskTime = tasks[i].timestamp.getTime();
    totalTimeInterval += currentTaskTime - previousTaskTime;
  }

  // Calculate average time in milliseconds
  const averageTimeInterval = totalTimeInterval / (tasks.length - 1);

  // Convert milliseconds to a more suitable time unit if needed, e.g., seconds or minutes
  const averageTimeInSeconds = averageTimeInterval / 1000;

  return averageTimeInSeconds;
}

function calculateStrategyPoints(
  individualAverageTime: number,
  strategy: Strategy,
  globalAverageTime: number,
  previousGlobalAverageTime?: number
): number {
  let points = 0;

  // Calculate points based on individual average time
  if (individualAverageTime < globalAverageTime) {
    // User performs better than the global average
    points += strategy.parameters.weightIndividualImprove;
  }

  // Calculate points based on global average time
  if (
    previousGlobalAverageTime &&
    individualAverageTime < previousGlobalAverageTime
  ) {
    // User performs better than the previous global average
    points += strategy.parameters.weightGlobalImprove;
  }

  return points;
}

export { PointsController };
