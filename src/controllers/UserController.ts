import { Request, Response } from "express";
import { UserModel } from "../models/UserModel";

class UserController {
  // Get a specific user by ID
  static async getUserById(req: Request, res: Response) {
    try {
      const userId = req.params.id;
      const user = await UserModel.findById(userId);
      if (!user) {
        return res.status(404).json({ message: "User not found" });
      }
      res.json(user);
    } catch (error) {
      res.status(500).send(error);
    }
  }

  // Delete a user
  static async deleteUser(req: Request, res: Response) {
    try {
      const userId = req.params.id;
      const deletedUser = await UserModel.findByIdAndDelete(userId);
      if (!deletedUser) {
        return res.status(404).json({ message: "User not found" });
      }
      res.status(200).json({ message: "User deleted successfully" });
    } catch (error) {
      res.status(500).send(error);
    }
  }
}

export { UserController };
