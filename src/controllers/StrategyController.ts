import { Request, Response } from "express";
import { StrategyModel, Strategy, GameModel } from "../models";

class StrategyController {
  // Retrieves the strategy for a specific game
  static async getStrategyForGame(req: Request, res: Response) {
    try {
      const { gameId } = req.params;
      if (!gameId) {
        return res.status(400).json({ message: "Game ID is required" });
      }

      // Find the game
      const game = await GameModel.findById(gameId).lean();
      if (!game) {
        return res.status(404).json({ message: "Game not found" });
      }

      const { strategy } = game;
      if (!strategy) {
        return res
          .status(404)
          .json({ message: "Strategy not found for this game" });
      }
      return res.status(200).json(strategy);
    } catch (error) {
      res.status(500).send(error);
    }
  }

  // Lists all available strategies
  static async listAllStrategies(req: Request, res: Response) {
    try {
      const strategies = await StrategyModel.find({});
      res.status(200).json(strategies);
    } catch (error) {
      console.error(error);
      res.status(500).send(error);
    }
  }

  static async createStrategy(req: Request, res: Response) {
    try {
      const body = req.body as Strategy;

      // Validate and sanitize input
      if (!body.name) {
        return res.status(400).json({ message: "Name is required" });
      }
      if (!body.description) {
        return res.status(400).json({ message: "Description is required" });
      }
      if (!body.strategyType) {
        return res.status(400).json({ message: "Strategy type is required" });
      }
      if (!body.parameters) {
        return res.status(400).json({ message: "Parameters are required" });
      }
      if (!body.cases) {
        return res.status(400).json({ message: "Cases are required" });
      }
      if (body?._id) {
        delete body._id;
      }
      // Create the strategy
      const newStrategy = new StrategyModel(body);
      await newStrategy.save();

      res.status(201).json({ message: "Strategy created successfully" });
    } catch (error) {
      console.error(error);
      res.status(500).json({ error: error });
    }
  }

  static async getStrategyById(req: Request, res: Response) {
    try {
      const { strategyId } = req.params;

      const strategy = await StrategyModel.findById(strategyId);
      if (!strategy) {
        return res.status(404).json({ message: "Strategy not found" });
      }

      res.status(200).json(strategy);
    } catch (error) {
      console.error(error);
      res.status(500).send(error);
    }
  }

  static async deleteStrategy(req: Request, res: Response) {
    try {
      const { strategyId } = req.params;

      // Optional: Check if any games are currently using this strategy
      const gamesUsingStrategy = await GameModel.find({
        currentStrategy: strategyId,
      });
      if (gamesUsingStrategy.length > 0) {
        return res.status(400).json({
          message: "Cannot delete strategy as it is currently in use by games",
        });
      }

      // Delete the strategy
      const strategy = await StrategyModel.findByIdAndDelete(strategyId);
      if (!strategy) {
        return res.status(404).json({ message: "Strategy not found" });
      }

      res.status(200).json({ message: "Strategy deleted successfully" });
    } catch (error) {
      console.error(error);
      res.status(500).send(error);
    }
  }

  static async listStrategiesByCriteria(req: Request, res: Response) {
    try {
      const { name, dateFrom, dateTo } = req.query;

      // Validate and sanitize criteria
      let query: any = {};
      if (name) {
        query.name = new RegExp(String(name), "i"); // Case-insensitive match for the name
      }

      if (dateFrom || dateTo) {
        query.createdAt = {};
        if (dateFrom) {
          query.createdAt.$gte = new Date(dateFrom as string);
        }
        if (dateTo) {
          query.createdAt.$lte = new Date(dateTo as string);
        }
      }

      // Find strategies based on criteria
      const strategies = await StrategyModel.find(query);
      if (strategies.length === 0) {
        return res
          .status(404)
          .json({ message: "No strategies found matching the given criteria" });
      }

      res.status(200).json(strategies);
    } catch (error) {
      console.error(error);
      res.status(500).send(error);
    }
  }
}

export { StrategyController };
