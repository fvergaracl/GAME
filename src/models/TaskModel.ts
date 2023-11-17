import { Document, model, Schema, Types } from "mongoose";

interface Task extends Document {
  timestamp: Date;
  idUser: Types.ObjectId;
  idGame: Types.ObjectId;
}

const taskSchema = new Schema<Task>({
  timestamp: { type: Date, default: Date.now },
  idUser: { type: Schema.Types.ObjectId, ref: "User", required: true },
  idGame: { type: Schema.Types.ObjectId, ref: "Game", required: true },
});

const TaskModel = model<Task>("Task", taskSchema);

export { TaskModel, Task };
