import { Request, Response } from "express";
import { StrategyModel, GameModel } from "../models";

class StrategyController {
  // Retrieves the strategy for a specific game
  static async getStrategyForGame(req: Request, res: Response) {
    try {
      const { gameId } = req.params;

      // Find the game
      const game = await GameModel.findById(gameId);
      if (!game) {
        return res.status(404).json({ message: "Game not found" });
      }

      // Retrieve the strategy using the game's current strategy ID
      const strategy = await StrategyModel.findById(game.currentStrategy);
      if (!strategy) {
        return res
          .status(404)
          .json({ message: "Strategy not found for this game" });
      }

      res.status(200).json(strategy);
    } catch (error) {
      console.error(error);
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
      const { name, description, strategyType, parameters, cases } = req.body;

      // Validate the required fields
      if (!name || !description || !strategyType || !parameters) {
        return res.status(400).json({
          message:
            "Name, description, strategyType, and parameters are required for strategy creation",
        });
      }

      // Convert cases to the required format if necessary
      const formattedCases: Record<string, any> = {};
      for (const [key, value] of Object.entries(cases || {})) {
        formattedCases[key] = {
          ...(value as Record<string, unknown>),
          subCases:
            value && typeof value === "object" && "subCases" in value
              ? new Map(
                  Object.entries(value.subCases as Record<string, unknown>)
                )
              : undefined,
        };
      }

      // Create a new strategy
      const newStrategy = new StrategyModel({
        name,
        description,
        strategyType,
        parameters,
        cases: formattedCases,
      });

      await newStrategy.save();

      res.status(201).json({
        message: "Strategy created successfully",
        strategy: newStrategy,
      });
    } catch (error) {
      console.error(error);
      res.status(500).send(error);
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

  static async copyStrategy(req: Request, res: Response) {
    try {
      const { strategyId } = req.params;
      const modifications = req.body; // Assuming any modifications to the strategy are sent in the request body

      // Find the original strategy
      const originalStrategy = await StrategyModel.findById(strategyId);
      if (!originalStrategy) {
        return res.status(404).json({ message: "Original strategy not found" });
      }

      // Create a new strategy based on the original
      const newStrategyData = {
        ...originalStrategy.toObject(),
        ...modifications,
        _id: undefined,
        createdAt: undefined,
        updatedAt: undefined,
      };

      const newStrategy = new StrategyModel(newStrategyData);
      await newStrategy.save();

      res
        .status(201)
        .json({ message: "Strategy copied successfully", newStrategy });
    } catch (error) {
      console.error(error);
      res.status(500).send(error);
    }
  }
}

export { StrategyController };
