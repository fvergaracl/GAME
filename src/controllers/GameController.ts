import { Request, Response } from "express";
import { GameModel, Game, StrategyModel } from "../models";

class GameController {
  // Create a new game
  static async createGame(req: Request, res: Response): Promise<void> {
    try {
      const body = req.body as Game;
      let currentStrategyId = body.currentStrategyId;
      // Validate and sanitize input
      if (!body.identification) {
        res.status(400).json({ message: "Identification is required" });
      }
      if (!body.timestampEnd) {
        res.status(400).json({ message: "End timestamp is required" });
      }
      if (!body.timestampStart) {
        res.status(400).json({ message: "Start timestamp is required" });
      }

      if (!body.createdBy) {
        res.status(400).json({ message: "Creator is required" });
      }
      const timestampEnd = new Date(body.timestampEnd);
      const timestampStart = new Date(body.timestampStart);
      if (body.timestampEnd && isNaN(timestampEnd.getTime())) {
        res.status(400).json({ message: "End timestamp is invalid" });
      }

      if (body.timestampEnd && isNaN(timestampStart.getTime())) {
        res.status(400).json({ message: "Start timestamp is invalid" });
      }

      if (body.timestampEnd <= body.timestampStart) {
        res
          .status(400)
          .json({ message: "End timestamp must be after start timestamp" });
      }
      let strategy;
      if (body.currentStrategyId) {
        strategy = await StrategyModel.findById(body.currentStrategyId);
        if (!strategy) {
          res.status(404).json({ message: "Strategy not found" });
        }
      }
      if (!body.currentStrategyId) {
        // get first strategy
        strategy = await StrategyModel.findOne({});
        if (!strategy) {
          res.status(404).json({ message: "Default Strategy not found" });
        }
        currentStrategyId = strategy?._id;
      }

      const newGame = new GameModel({
        ...body,
        strategy,
        createdAt: new Date(),
      });

      const newGameSaved = await newGame.save();

      res.status(201).json({
        message: "Game created successfully",
        stategyId: currentStrategyId,
        game: newGameSaved._id,
      });
    } catch (error) {
      console.log(error);
      res.status(500).send(error);
    }
  }

  // Get a list of all games
  static async getAllGames(_: Request, res: Response) {
    try {
      const games = await GameModel.find({});
      res.status(200).json(games);
    } catch (error) {
      res.status(500).send(error);
    }
  }

  // Get a single game by ID
  static async getGameById(req: Request, res: Response): Promise<void> {
    try {
      const gameId = req.params["gameId"];
      const game = await GameModel.findById(gameId);
      if (!game) {
        res.status(404).json({ message: "Game not found" });
      }
      res.status(200).json(game);
    } catch (error) {
      res.status(500).send(error);
    }
  }

  // Delete a game
  /*
  static async deleteGame(req: Request, res: Response) {
    try {
      const gameId = req.params.gameId;
      const deletedGame = await GameModel.findByIdAndDelete(gameId);
      if (!deletedGame) {
        return res.status(404).json({ message: "Game not found" });
      }
      res.status(200).json({ message: "Game deleted successfully" });
    } catch (error) {
      res.status(500).send(error);
    }
  }
   */
}

export { GameController };
