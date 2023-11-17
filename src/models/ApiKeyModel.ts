import { Document, model, Schema } from "mongoose";

interface ApiKey extends Document {
  key: string;
  toolName: string;
  creationDate: Date;
  expirationDate?: Date; // Optional
}

const apiKeySchema = new Schema<ApiKey>({
  key: {
    type: String,
    required: true,
    unique: true,
  },
  toolName: {
    type: String,
    required: true,
  },
  creationDate: {
    type: Date,
    default: Date.now,
  },
  expirationDate: {
    type: Date,
    required: false,
  },
});

const ApiKeyModel = model<ApiKey>("ApiKey", apiKeySchema);

export { ApiKeyModel };
