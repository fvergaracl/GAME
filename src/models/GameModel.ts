import { Document, model, Schema, Types } from "mongoose";
import { Strategy, strategySchema } from "./StrategyModel";

interface Game extends Document {
  identification: string;
  timestampEnd: Date;
  timestampStart: Date;
  currentStrategyId: Types.ObjectId; // Reference to the current strategy model
  strategy?: Strategy; // Optional
  description?: string; // Optional
  createdBy: string;
  createdAt?: Date;
}

const gameSchema = new Schema<Game>(
  {
    identification: { type: String, required: true },
    timestampEnd: { type: Date },
    timestampStart: { type: Date, default: Date.now },
    strategy: { type: strategySchema, required: false },
    description: { type: String },
    createdBy: { type: String, required: true },
    createdAt: { type: Date, default: Date.now },
  },
  { versionKey: false }
);

const GameModel = model<Game>("Game", gameSchema);

export { GameModel, Game, gameSchema };
