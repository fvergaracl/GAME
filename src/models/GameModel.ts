import { Document, model, Schema, Types } from "mongoose";

interface Game extends Document {
  identification: string;
  timestampEnd: Date;
  timestampStart: Date;
  currentStrategy: Types.ObjectId; // Reference to the current strategy model
  description?: string; // Optional
  defaultPointsTaskCampaign: number;
  createdBy: string;
}

const gameSchema = new Schema<Game>({
  identification: { type: String, required: true },
  timestampEnd: { type: Date },
  timestampStart: { type: Date, default: Date.now },
  currentStrategy: {
    type: Schema.Types.ObjectId,
    ref: "Strategy",
    required: true,
  },
  description: { type: String },
  defaultPointsTaskCampaign: { type: Number, required: true },
});

const GameModel = model<Game>("Game", gameSchema);

export { GameModel };
