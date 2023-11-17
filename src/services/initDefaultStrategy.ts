const initDefaultStrategy = {
  name: "StandardGamificationStrategy",
  description:
    "Strategy to calculate points based on individual and global behavior.",
  strategyType: "BehaviorBasedPoints",
  parameters: {
    defaultPointsTaskCampaign: 10,
    weightIndividualImprove: 10,
    weightGlobalImprove: 10,
    cases: {
      case1: {
        description:
          "First or second task of the user without global behavior data.",
        calculatePoints: "defaultPointsTaskCampaign",
      },
      case2: {
        description:
          "Second task of the user with available global behavior data.",
        subCases: {
          "2.1": {
            condition: "timeInvestedLastTask > globalCalculation",
            calculatePoints: "defaultPointsTaskCampaign",
          },
          "2.2": {
            condition: "timeInvestedLastTask < globalCalculation",
            calculatePoints: "defaultPointsTaskCampaign + Bonus",
          },
        },
      },
      case3: {
        description: "Individual behavior data available, no global behavior.",
        calculatePoints: "defaultPointsTaskCampaign",
      },
      case4: {
        description: "Complete individual and global behavior data.",
        subCases: {
          "4.1": {
            condition:
              "timeInvestedLastTask < individualCalculation AND timeInvestedLastTask > globalCalculation",
            calculatePoints: "FormulaBased",
          },
          "4.2": {
            condition:
              "timeInvestedLastTask > individualCalculation AND timeInvestedLastTask > globalCalculation",
            calculatePoints: "defaultPointsTaskCampaign",
          },
          "4.3": {
            condition:
              "timeInvestedLastTask < individualCalculation AND timeInvestedLastTask < globalCalculation",
            calculatePoints: "FormulaBasedMaxBonus",
          },
          "4.4": {
            condition:
              "timeInvestedLastTask > individualCalculation AND timeInvestedLastTask < globalCalculation",
            calculatePoints: "defaultPointsTaskCampaign + MinorBonus",
          },
        },
      },
    },
  },
};

export { initDefaultStrategy };
