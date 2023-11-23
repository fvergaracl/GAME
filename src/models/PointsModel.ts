import { Document, model, Schema, Types } from "mongoose";
import { Game, gameSchema } from "./GameModel";
import { Task, taskSchema } from "./TaskModel";

interface Points extends Document {
  userId: string;
  game?: Game;
  task?: Task;
  points?: number;
  formula?: string;
  createdAt?: Date;
}

const pointsSchema = new Schema<Points>({
  userId: { type: String, required: true },
  game: { type: gameSchema, required: true },
  task: { type: taskSchema, required: false },
  points: { type: Number, required: true },
  formula: { type: String, required: true },
  createdAt: { type: Date, default: Date.now },
});

const PointsModel = model<Points>("Points", pointsSchema);

export { PointsModel, Points };
