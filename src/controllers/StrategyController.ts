import { Request, Response } from "express";
import { Strategy, Game } from "../models";

class StrategyController {
  // Retrieves the strategy for a specific game
  static async getStrategyForGame(req: Request, res: Response): Promise<void> {
    try {
      const { gameId } = req.params;
      if (!gameId) {
        res.status(400).json({ message: "Game ID is required" });
        return;
      }

      // Buscar el juego
      const game = await Game.findByPk(gameId);
      if (!game) {
        res.status(404).json({ message: "Game not found" });
        return;
      }

      // Suponiendo que 'strategy' es una relación o un campo en el modelo de 'Game'
      // Si 'strategy' es un ID o clave foránea, deberás realizar otra consulta para obtener la estrategia
      const strategyId = game.strategy; // O la forma apropiada de obtener el ID de la estrategia del juego
      if (!strategyId) {
        res.status(404).json({ message: "Strategy not found for this game" });
        return;
      }

      const strategy = await Strategy.findByPk(strategyId.toString());
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

      // Validar y sanitizar la entrada
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

      // Crear la estrategia
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

  // static async getStrategyById(req: Request, res: Response) {
  //   try {
  //     const { strategyId } = req.params;

  //     const strategy = await StrategyModel.findById(strategyId);
  //     if (!strategy) {
  //       res.status(404).json({ message: "Strategy not found" });
  //     }

  //     res.status(200).json(strategy);
  //   } catch (error) {
  //     console.error(error);
  //     res.status(500).send(error);
  //   }
  // }

  // static async deleteStrategy(req: Request, res: Response) {
  //   try {
  //     const { strategyId } = req.params;

  //     // Optional: Check if any games are currently using this strategy
  //     const gamesUsingStrategy = await GameModel.find({
  //       currentStrategy: strategyId,
  //     });
  //     if (gamesUsingStrategy.length > 0) {
  //       res.status(400).json({
  //         message: "Cannot delete strategy as it is currently in use by games",
  //       });
  //     }

  //     // Delete the strategy
  //     const strategy = await StrategyModel.findByIdAndDelete(strategyId);
  //     if (!strategy) {
  //       res.status(404).json({ message: "Strategy not found" });
  //     }

  //     res.status(200).json({ message: "Strategy deleted successfully" });
  //   } catch (error) {
  //     console.error(error);
  //     res.status(500).send(error);
  //   }
  // }

  // static async listStrategiesByCriteria(req: Request, res: Response) {
  //   try {
  //     const { name, dateFrom, dateTo } = req.query;

  //     // Validate and sanitize criteria
  //     const query: any = {};
  //     if (name) {
  //       query.name = new RegExp(String(name), "i"); // Case-insensitive match for the name
  //     }

  //     if (dateFrom || dateTo) {
  //       query.createdAt = {};
  //       if (dateFrom) {
  //         query.createdAt.$gte = new Date(dateFrom as string);
  //       }
  //       if (dateTo) {
  //         query.createdAt.$lte = new Date(dateTo as string);
  //       }
  //     }

  //     // Find strategies based on criteria
  //     const strategies = await StrategyModel.find(query);
  //     if (strategies.length === 0) {
  //       res
  //         .status(404)
  //         .json({ message: "No strategies found matching the given criteria" });
  //     }

  //     res.status(200).json(strategies);
  //   } catch (error) {
  //     console.error(error);
  //     res.status(500).send(error);
  //   }
  // }
}

export { StrategyController };
