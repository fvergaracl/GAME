import { Document, model, Schema, Types } from "mongoose";

interface Points extends Document {
  idUser: Types.ObjectId;
  idGame: Types.ObjectId;
  points: number;
  strategyUsed: Types.ObjectId; // Strategy used for this points allocation
}

const pointsSchema = new Schema<Points>({
  idUser: { type: Schema.Types.ObjectId, ref: "User", required: true },
  idGame: { type: Schema.Types.ObjectId, ref: "Game", required: true },
  points: { type: Number, required: true },
  strategyUsed: {
    type: Schema.Types.ObjectId,
    ref: "Strategy",
    required: true,
  },
});

const PointsModel = model<Points>("Points", pointsSchema);

export { PointsModel };
