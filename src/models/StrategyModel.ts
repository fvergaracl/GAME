import { Document, model, Schema } from "mongoose";

interface CaseSub {
  criteria: string;
  formula: string;
}

interface Case {
  criteria: string;
  formula: string;
  subCases?: Record<string, CaseSub>;
}

interface StrategyParameters {
  BASIC_POINTS: number;
  BONUS_FACTOR?: number;
  SMALLER_BONUS?: number;
  INDIVIDUAL_IMPROVEMENT_FACTOR?: number;
  WEIGHT_GLOBAL_IMPROVE?: number;
  WEIGHT_INDIVIDUAL_IMPROVE?: number;
}

interface Strategy extends Document {
  name: string;
  description: string;
  strategyType: string;
  parameters: StrategyParameters;
  cases: Case[];
}

const caseSubSchema = new Schema<CaseSub>({
  criteria: { type: String, required: true },
  formula: { type: String, required: true },
});

const caseSchema = new Schema<Case>(
  {
    criteria: { type: String, required: true },
    formula: { type: String },
    subCases: {
      type: Map,
      of: caseSubSchema,
    },
  },
  { _id: false }
);

const strategyParametersSchema = new Schema<StrategyParameters>(
  {
    BASIC_POINTS: { type: Number, required: true },
    BONUS_FACTOR: { type: Number },
    SMALLER_BONUS: { type: Number },
    INDIVIDUAL_IMPROVEMENT_FACTOR: { type: Number },
    WEIGHT_GLOBAL_IMPROVE: { type: Number },
    WEIGHT_INDIVIDUAL_IMPROVE: { type: Number },
  },
  { _id: false }
);

const strategySchema = new Schema<Strategy>(
  {
    name: { type: String, required: true },
    description: { type: String, required: true },
    strategyType: { type: String, required: true },
    parameters: { type: strategyParametersSchema, required: true },
    cases: [caseSchema],
  },
  { versionKey: false }
);

const StrategyModel = model<Strategy>("Strategy", strategySchema);

export {
  StrategyModel,
  Strategy,
  StrategyParameters,
  strategySchema,
  caseSubSchema,
  CaseSub,
};
