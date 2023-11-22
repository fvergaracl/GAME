import { Document, model, Schema, Types } from "mongoose";
import {
  Strategy,
  strategySchema,
  caseSubSchema,
  CaseSub,
} from "./StrategyModel";

interface Points extends Document {
  idUser: string;
  idGame: Types.ObjectId;
  idTask?: Types.ObjectId;
  points?: number;
  strategy?: Strategy;
  strategyUsed?: CaseSub; // Strategy used for this points allocation
}

const pointsSchema = new Schema<Points>({
  idUser: { type: String, required: true },
  idGame: { type: Schema.Types.ObjectId, ref: "Game", required: true },
  idTask: { type: Schema.Types.ObjectId, ref: "Task", required: false },
  points: { type: Number, required: true },
  strategy: { type: strategySchema, required: true },
  strategyUsed: { type: caseSubSchema, required: true },
});

const PointsModel = model<Points>("Points", pointsSchema);

export { PointsModel, Points };
