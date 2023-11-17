import { Document, model, Schema, Types } from "mongoose";

interface Game extends Document {
  identification: string;
  timestampEnd: Date;
  timestampStart: Date;
  idStrategy?: Types.ObjectId; // Optional, reference to another model if needed
  description?: string; // Optional
  defaultPointsTaskCampaign: number;
  weightIndividualImprove: number;
  weightGlobalImprove: number;
}

const gameSchema = new Schema<Game>({
  identification: { type: String, required: true },
  timestampEnd: { type: Date },
  timestampStart: { type: Date, default: Date.now },
  idStrategy: { type: Schema.Types.ObjectId, ref: "Strategy", required: false },
  description: { type: String, required: false },
  defaultPointsTaskCampaign: { type: Number, required: true },
  weightIndividualImprove: { type: Number, required: true },
  weightGlobalImprove: { type: Number, required: true },
});

const GameModel = model<Game>("Game", gameSchema);

export { GameModel };
