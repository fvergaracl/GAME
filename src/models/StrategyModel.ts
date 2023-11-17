import { Document, model, Schema } from "mongoose";

interface CaseSub {
  condition: string;
  calculatePoints: string;
}

interface Case {
  description: string;
  calculatePoints?: string;
  subCases?: Record<string, CaseSub>;
}

interface StrategyParameters {
  defaultPointsTaskCampaign: number;
  weightIndividualImprove: number;
  weightGlobalImprove: number;
  minorBonus: number;
}

interface Strategy extends Document {
  name: string;
  description: string;
  strategyType: string;
  parameters: StrategyParameters;
  cases: Record<string, Case>;
}

const caseSubSchema = new Schema<CaseSub>({
  condition: { type: String, required: true },
  calculatePoints: { type: String, required: true },
});

const caseSchema = new Schema<Case>({
  description: { type: String, required: true },
  calculatePoints: { type: String },
  subCases: {
    type: Map,
    of: caseSubSchema,
  },
});

const strategyParametersSchema = new Schema<StrategyParameters>({
  defaultPointsTaskCampaign: { type: Number, required: true },
  weightIndividualImprove: { type: Number, required: true },
  weightGlobalImprove: { type: Number, required: true },
  minorBonus: { type: Number, required: true },
});

const strategySchema = new Schema<Strategy>({
  name: { type: String, required: true },
  description: { type: String, required: true },
  strategyType: { type: String, required: true },
  parameters: { type: strategyParametersSchema, required: true },
  cases: {
    type: Map,
    of: caseSchema,
  },
});

const StrategyModel = model<Strategy>("Strategy", strategySchema);

export { StrategyModel, Strategy };
