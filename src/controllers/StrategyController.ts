import { Request, Response } from "express";
import { Strategy, Game } from "../models";

class StrategyController {
  // Retrieves the strategy for a specific game
  static async getStrategyForGame(req: Request, res: Response): Promise<void> {
    try {
      const { gameId } = req.params;

      const game = await Game.findByPk(gameId);

      if (!game) {
        res.status(404).json({ message: "Game not found" });
        return;
      }

      const currentStrategyId = game.currentStrategyId;

      const strategy = await Strategy.findByPk(currentStrategyId);

      if (!strategy) {
        res.status(404).json({ message: "Strategy not found" });
        return;
      }

      res.status(200).json(strategy);
    } catch (error) {
      console.error(error);
      res.status(500).json({ error: error });
    }
  }

  // Lists all available strategies
  static async listAllStrategies(req: Request, res: Response): Promise<void> {
    try {
      const strategies = await Strategy.findAll();
      res.status(200).json(strategies);
    } catch (error) {
      console.error(error);
      res.status(500).json({ error: error });
    }
  }

  static async createStrategy(req: Request, res: Response): Promise<void> {
    try {
      const { name, description, strategyType, parameters, cases } = req.body;

      if (!name) {
        res.status(400).json({ message: "Name is required" });
        return;
      }
      if (!description) {
        res.status(400).json({ message: "Description is required" });
        return;
      }
      if (!strategyType) {
        res.status(400).json({ message: "Strategy type is required" });
        return;
      }
      if (!parameters) {
        res.status(400).json({ message: "Parameters are required" });
        return;
      }
      if (!cases) {
        res.status(400).json({ message: "Cases are required" });
        return;
      }

      const newStrategy = await Strategy.create({
        name,
        description,
        strategyType,
        parameters,
        cases,
      });

      res.status(201).json({
        message: "Strategy created successfully",
        strategy: newStrategy,
      });
    } catch (error) {
      console.error(error);
      res.status(500).json({ error });
    }
  }

  static async getStrategyById(req: Request, res: Response) {
    try {
      const { strategyId } = req.params;

      const strategy = await Strategy.findByPk(strategyId);
      if (!strategy) {
        res.status(404).json({ message: "Strategy not found" });
      }

      res.status(200).json(strategy);
    } catch (error) {
      console.error(error);
      res.status(500).send(error);
    }
  }
}

export { StrategyController };
