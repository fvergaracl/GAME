type StrategyParameters = {
  BASIC_POINTS: number;
  BONUS_FACTOR: number;
  SMALLER_BONUS: number;
  WEIGHT_GLOBAL_IMPROVE: number;
  WEIGHT_INDIVIDUAL_IMPROVE: number;
};

type TaskData = {
  TIME_INVESTED_LAST_TASK?: number | undefined;
  GLOBAL_AVERAGE?: number | undefined;
  USER_AVERAGE?: number | undefined;
};

function parseAndComputeFormula(
  formula: string,
  params: StrategyParameters,
  taskData: TaskData
): number {
  // FORMULA_BASIC_POINTS
  // FORMULA_GLOBAL_AVERAGE_COMPARISON
  // FORMULA_USER_AVERAGE_COMPARISON
  // FORMULA_GLOBAL_AND_INDIVIDUAL_IMPROVEMENT
  if (formula === "FORMULA_BASIC_POINTS") {
    // BASIC_POINTS
    return params.BASIC_POINTS;
  }
  if (formula === "FORMULA_GLOBAL_AVERAGE_COMPARISON") {
    if (taskData?.GLOBAL_AVERAGE && taskData?.TIME_INVESTED_LAST_TASK) {
      // BASIC_POINTS + (TIME_INVESTED_LAST_TASK > GLOBAL_AVERAGE ? SMALLER_BONUS : BONUS_FACTOR)
      return (
        params.BASIC_POINTS +
        (taskData.TIME_INVESTED_LAST_TASK > taskData.GLOBAL_AVERAGE
          ? params.SMALLER_BONUS
          : params.BONUS_FACTOR)
      );
    }
    return -1;
  }
  if (formula === "FORMULA_USER_AVERAGE_COMPARISON") {
    if (taskData?.USER_AVERAGE && taskData?.TIME_INVESTED_LAST_TASK) {
      // BASIC_POINTS + (TIME_INVESTED_LAST_TASK > USER_AVERAGE ? SMALLER_BONUS : BONUS_FACTOR)
      return (
        params.BASIC_POINTS +
        (taskData.TIME_INVESTED_LAST_TASK > taskData.USER_AVERAGE
          ? params.SMALLER_BONUS
          : params.BONUS_FACTOR)
      );
    }
    return -1;
  }
  if (formula === "FORMULA_GLOBAL_AND_INDIVIDUAL_IMPROVEMENT") {
    // BASIC_POINTS + WEIGHT_GLOBAL_IMPROVE * max[0, (GLOBAL_AVERAGE - TIME_INVESTED_LAST_TASK)/GLOBAL_AVERAGE] + WEIGHT_INDIVIDUAL_IMPROVE * max[0, (USER_AVERAGE - TIME_INVESTED_LAST_TASK)/USER_AVERAGE]
    if (
      taskData?.GLOBAL_AVERAGE &&
      taskData?.TIME_INVESTED_LAST_TASK &&
      taskData?.USER_AVERAGE
    ) {
      const factorIndividual =
        taskData.USER_AVERAGE > 0
          ? (taskData.USER_AVERAGE - taskData.TIME_INVESTED_LAST_TASK) /
            taskData.USER_AVERAGE
          : 0;
      const factorGlobal =
        taskData.GLOBAL_AVERAGE > 0
          ? (taskData.GLOBAL_AVERAGE - taskData.TIME_INVESTED_LAST_TASK) /
            taskData.GLOBAL_AVERAGE
          : 0;

      const positiveFactorIndividual = Math.max(0, factorIndividual);
      const positiveFactorGlobal = Math.max(0, factorGlobal);

      const points =
        params.WEIGHT_INDIVIDUAL_IMPROVE * positiveFactorIndividual +
        params.WEIGHT_GLOBAL_IMPROVE * positiveFactorGlobal;

      return points;
    }
    return -1;
  }
  return -1;
}
