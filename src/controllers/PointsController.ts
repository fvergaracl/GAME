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
  /*
  router.get("/:userId", PointsController.getUserPoints);
router.get("/:userId/:taskId", PointsController.getUserPointsInTask);
router.get("/:userId/:gameId", PointsController.getUserPointsInGame);
  */

  static async getUserPoints(req: Request, res: Response) {
    try {
      res.status(200).json({ message: "getUserPoints" });
    } catch (error) {
      res.status(500).json({ message: "getUserPoints -ERROR" });
    }
  }

  static async getUserPointsInTask(req: Request, res: Response) {
    try {
      res.status(200).json({ message: "getUserPointsInTask" });
    } catch (error) {
      res.status(500).json({ message: "getUserPointsInTask -ERROR" });
    }
  }

  static async getUserPointsInGame(req: Request, res: Response) {
    try {
      res.status(200).json({ message: "getUserPointsInGame" });
    } catch (error) {
      res.status(500).json({ message: "getUserPointsInGame -ERROR" });
    }
  }
  static async assignPointsToUser(req: Request, res: Response) {
    try {
    } catch (error) {}
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

export { PointsController };
