const initDefaultStrategyJson = {
  name: "StandardGamificationStrategy",
  description:
    "Strategy to calculate points based on individual and global behavior.",
  strategyType: "BehaviorBasedPoints",
  parameters: {
    BASIC_POINTS: 10,
    BONUS_FACTOR: 1.5,
    SMALLER_BONUS: 0.5,
    INDIVIDUAL_IMPROVEMENT_FACTOR: 1.5,
    WEIGHT_GLOBAL_IMPROVE: 0.5,
    WEIGHT_INDIVIDUAL_IMPROVE: 0.5,
    cases: [
      {
        criteria: "EARLY_TASK_NO_GLOBAL",
        formula: "FORMULA_BASIC_POINTS",
      },
      {
        criteria: "SECOND_TASK_GLOBAL_DATA",
        formula: "FORMULA_GLOBAL_AVERAGE_COMPARISON",
      },
      {
        criteria: "INDIVIDUAL_DATA_NO_GLOBAL",
        formula: "FORMULA_USER_AVERAGE_COMPARISON",
      },
      {
        criteria: "BOTH_INDIVIDUAL_GLOBAL_DATA",
        formula: "FORMULA_GLOBAL_AND_INDIVIDUAL_IMPROVEMENT",
      },
    ],
  },
};

import { StrategyModel } from "../models";

const initDefaultStrategy = async () => {
  try {
    console.log("Initializing default strategy...");
    const existingStrategy = await StrategyModel.findOne({
      name: initDefaultStrategyJson.name,
    });

    if (!existingStrategy) {
      const newStrategy = new StrategyModel(initDefaultStrategyJson);
      await newStrategy.save();
      console.log(`Created default strategy`);
    }

    console.log("Default strategy initialized");
  } catch (error) {
    console.error("Error initializing default strategy:", error);
  }
};

export { initDefaultStrategy };
