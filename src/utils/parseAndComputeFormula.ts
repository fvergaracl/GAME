type StrategyParameters = {
  BASIC_POINTS: number;
  BONUS_FACTOR: number;
  SMALLER_BONUS: number;
  WEIGHT_GLOBAL_IMPROVE: number;
  WEIGHT_INDIVIDUAL_IMPROVE: number;
};

type TaskData = {
  TIME_INVESTED_LAST_TASK: number;
  GLOBAL_AVERAGE: number;
  USER_AVERAGE: number;
};

function parseAndComputeFormula(
  formula: string,
  params: StrategyParameters,
  taskData: TaskData
): number {
  if (formula.includes("BASIC_POINTS + WEIGHT_GLOBAL_IMPROVE")) {
    // Handling the first formula
    const globalImprovement = Math.max(
      0,
      (taskData.GLOBAL_AVERAGE - taskData.TIME_INVESTED_LAST_TASK) /
        taskData.GLOBAL_AVERAGE
    );
    const individualImprovement = Math.max(
      0,
      (taskData.USER_AVERAGE - taskData.TIME_INVESTED_LAST_TASK) /
        taskData.USER_AVERAGE
    );
    return (
      params.BASIC_POINTS +
      params.WEIGHT_GLOBAL_IMPROVE * globalImprovement +
      params.WEIGHT_INDIVIDUAL_IMPROVE * individualImprovement
    );
  } else if (
    formula.includes("BASIC_POINTS + (TIME_INVESTED_LAST_TASK > USER_AVERAGE")
  ) {
    // Handling the second formula
    return (
      params.BASIC_POINTS +
      (taskData.TIME_INVESTED_LAST_TASK > taskData.USER_AVERAGE
        ? -params.SMALLER_BONUS
        : params.BONUS_FACTOR)
    );
  } else {
    // Default case if the formula does not match the expected patterns
    return 0;
  }
}
