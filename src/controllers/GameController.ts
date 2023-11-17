import { Request, Response } from "express";
import { GameModel } from "../models";

class GameController {
  // Create a new game
  static async createGame(req: Request, res: Response) {
    try {
      const newGame = new GameModel(req.body); // Assuming game details are sent in request body
      await newGame.save();
      res.status(201).json(newGame);
    } catch (error) {
      res.status(500).send(error);
    }
  }

  // Get a list of all games
  static async getAllGames(req: Request, res: Response) {
    try {
      const games = await GameModel.find({});
      res.json(games);
    } catch (error) {
      res.status(500).send(error);
    }
  }

  // Get a single game by ID
  static async getGameById(req: Request, res: Response) {
    try {
      const gameId = req.params.gameId;
      const game = await GameModel.findById(gameId);
      if (!game) {
        return res.status(404).json({ message: "Game not found" });
      }
      res.json(game);
    } catch (error) {
      res.status(500).send(error);
    }
  }

  // Update a game
  static async updateGame(req: Request, res: Response) {
    try {
      const gameId = req.params.gameId;
      const updatedGame = await GameModel.findByIdAndUpdate(gameId, req.body, {
        new: true,
      });
      if (!updatedGame) {
        return res.status(404).json({ message: "Game not found" });
      }
      res.json(updatedGame);
    } catch (error) {
      res.status(500).send(error);
    }
  }

  // Delete a game
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
}

export { GameController };
