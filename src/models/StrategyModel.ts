import { Document, model, Schema, Types } from "mongoose";

interface StrategyCaseSubCase {
  condition: string;
  calculatePoints: string;
}

interface StrategyCase {
  description: string;
  calculatePoints?: string;
  subCases?: Record<string, StrategyCaseSubCase>;
}

interface StrategyParameters {
  defaultPointsTaskCampaign: number;
  weightIndividualImprove: number;
  weightGlobalImprove: number;
  minorBonus: number;
  cases: Record<string, StrategyCase>;
}

interface Strategy extends Document {
  name: string;
  description?: string;
  strategyType: string;
  parameters: StrategyParameters;
}

const strategyCaseSubCaseSchema = new Schema<StrategyCaseSubCase>({
  condition: { type: String, required: true },
  calculatePoints: { type: String, required: true },
});

const strategyCaseSchema = new Schema<StrategyCase>({
  description: { type: String, required: true },
  calculatePoints: { type: String },
  subCases: { type: Map, of: strategyCaseSubCaseSchema },
});

const strategyParametersSchema = new Schema<StrategyParameters>({
  defaultPointsTaskCampaign: { type: Number, required: true },
  weightIndividualImprove: { type: Number, required: true },
  weightGlobalImprove: { type: Number, required: true },
  cases: { type: Map, of: strategyCaseSchema, required: true },
});

const strategySchema = new Schema<Strategy>({
  name: { type: String, required: true },
  description: { type: String, required: false },
  strategyType: { type: String, required: true },
  parameters: { type: strategyParametersSchema, required: true },
});

const StrategyModel = model<Strategy>("Strategy", strategySchema);

export { StrategyModel };
