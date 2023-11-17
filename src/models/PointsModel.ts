import { Document, model, Schema, Types } from "mongoose";

interface Points extends Document {
  idUser: Types.ObjectId;
  idGame: Types.ObjectId;
  points: number;
}

const pointsSchema = new Schema<Points>({
  idUser: { type: Schema.Types.ObjectId, ref: "User", required: true },
  idGame: { type: Schema.Types.ObjectId, ref: "Game", required: true },
  points: { type: Number, required: true },
});

const PointsModel = model<Points>("Points", pointsSchema);

export { PointsModel };
