import { Request, Response } from "express";
import { Game, Strategy, CreateGameBody } from "../models";

class GameController {
  // Create a new game

  static async createGame(req: Request, res: Response): Promise<void> {
    try {
      const body = req.body as CreateGameBody;
      const {
        currentStrategyId,
        startDateTime,
        endDateTime,
        description,
        gameId,
      } = body;

      if (!currentStrategyId) {
        res.status(400).json({ message: "Current Strategy is required" });
        return;
      }

      if (!gameId) {
        res.status(400).json({ message: "Game ID is required" });
        return;
      }

      const gameWithSameId = await Game.findOne({
        where: { gameId: gameId },
      });

      if (gameWithSameId) {
        res.status(400).json({ message: "Game ID already exists" });
        return;
      }

      const strategyData: Strategy | null = await Strategy.findOne({
        where: { id: currentStrategyId },
      });

      if (!strategyData) {
        res.status(404).json({ message: "Strategy not found" });
        return;
      }

      const newGame = await Game.create({
        startDateTime: startDateTime || new Date(),
        gameId: gameId,
        endDateTime: endDateTime,
        description,
        currentStrategyId,
      });

      res.status(201).json({
        message: "Game created successfully",
        game: newGame,
      });
    } catch (error) {
      console.error(error);
      res.status(500).send(error);
    }
  }

  //getAllGames
  static async getAllGames(req: Request, res: Response): Promise<void> {
    try {
      const games = await Game.findAll({
        include: [Strategy],
      });

      res.status(200).json(games);
    } catch (error) {
      console.error(error);
      res.status(500).send(error);
    }
  }

  static async getGameByGameId(req: Request, res: Response): Promise<void> {
    try {
      const gameId = req.params['gameId']

      if (!gameId) {
        res.status(400).json({ message: "Game ID is required" });
        return;
      }

      const game = await Game.findOne({
        where: { gameId: gameId },
        include: [Strategy],
      });

      if (!game) {
        res.status(404).json({ message: "Game not found" });
      }

      res.status(200).json(game);
    } catch (error) {
      res.status(500).send(error);
    }
  }
}

export { GameController };
