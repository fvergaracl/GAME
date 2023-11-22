import { Document, model, Schema, Types } from "mongoose";
import { Game, gameSchema } from "./GameModel";
interface Task extends Document {
  name: string;
  description?: string;
  idGame?: Types.ObjectId;
  game?: Game;
  createdBy: string;
  createdAt?: Date;
}

const taskSchema = new Schema<Task>(
  {
    name: { type: String, required: true },
    description: { type: String, required: false },
    idGame: { type: Types.ObjectId, required: false },
    game: { type: gameSchema, required: false },
    createdBy: { type: String, required: true },
    createdAt: { type: Date, default: Date.now },
  },
  { versionKey: false }
);

const TaskModel = model<Task>("Task", taskSchema);

export { TaskModel, Task, taskSchema };
