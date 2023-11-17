import { Document, model, Schema } from "mongoose";

interface User extends Document {
  userId: string;
}

const userSchema = new Schema<User>({
  userId: { type: String, required: true, unique: true },
});

const UserModel = model<User>("User", userSchema);

export { UserModel };
