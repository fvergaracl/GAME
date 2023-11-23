import { Document, model, Schema } from "mongoose";

interface Action {
  name: string;
  timestamp: number;
}

interface User extends Document {
  userId: string;
  actions?: Action[] | [];
}

const actionSchema = new Schema<Action>({
  name: { type: String, required: true },
  timestamp: { type: Number, default: Date.now },
});

const userSchema = new Schema<User>(
  {
    userId: { type: String, required: true, unique: true },
    actions: { type: [actionSchema], default: [] },
  },
  { versionKey: false }
);

const UserModel = model<User>("User", userSchema);

export { UserModel };
