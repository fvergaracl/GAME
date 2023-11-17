import { Document, model, Schema, Types } from "mongoose";

interface GlobalBehavior extends Document {
  gameId: Types.ObjectId;
  averageTime: number;
  previousAverageTime?: number;
  totalTasks: number;
}

const globalBehaviorSchema = new Schema<GlobalBehavior>({
  gameId: { type: Schema.Types.ObjectId, ref: "Game", required: true },
  averageTime: { type: Number, required: true },
  previousAverageTime: { type: Number, required: false },
  totalTasks: { type: Number, required: true },
});

const GlobalBehaviorModel = model<GlobalBehavior>(
  "GlobalBehavior",
  globalBehaviorSchema
);

export { GlobalBehaviorModel };
