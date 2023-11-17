import { Document, model, Schema, Types } from "mongoose";

interface User extends Document {
  userId: string;
  games: [
    {
      gameId: Types.ObjectId;
      points: number; // Points in each game
      strategyUsed: Types.ObjectId; // Strategy used for point allocation
    }
  ];
}

const userSchema = new Schema<User>({
  userId: { type: String, required: true, unique: true },
  games: [
    {
      gameId: { type: Schema.Types.ObjectId, ref: "Game", required: true },
      points: { type: Number, default: 0 },
      strategyUsed: { type: Schema.Types.ObjectId, ref: "Strategy" },
    },
  ],
});

const UserModel = model<User>("User", userSchema);

export { UserModel };
