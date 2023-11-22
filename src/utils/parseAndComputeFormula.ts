import { Interface } from "readline";
import { StrategyParameters } from "../models";

type TaskData = {
  TIME_INVESTED_LAST_TASK?: number | undefined;
  GLOBAL_AVERAGE?: number | undefined;
  USER_AVERAGE?: number | undefined;
};

function calculateAverage(numbers: number[]): number {
  if (numbers.length === 0) {
    return 0;
  }
  const sum = numbers.reduce((total, num) => total + num, 0);
  return sum / numbers.length;
}

interface IResponse {
  formula: string | null;
  points: number;
}

const formulaGlobalAndIndividualImprove = (
  params: StrategyParameters,
  taskData: TaskData
): IResponse => {
  // BASIC_POINTS + WEIGHT_GLOBAL_IMPROVE * max[0, (GLOBAL_AVERAGE - TIME_INVESTED_LAST_TASK)/GLOBAL_AVERAGE] + WEIGHT_INDIVIDUAL_IMPROVE * max[0, (USER_AVERAGE - TIME_INVESTED_LAST_TASK)/USER_AVERAGE]
  let points = 0;
  const formula = "FORMULA_GLOBAL_AND_INDIVIDUAL_IMPROVEMENT";
  if (
    taskData?.GLOBAL_AVERAGE &&
    taskData?.TIME_INVESTED_LAST_TASK &&
    taskData?.USER_AVERAGE &&
    params?.WEIGHT_GLOBAL_IMPROVE &&
    params?.WEIGHT_INDIVIDUAL_IMPROVE
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

    points =
      params.WEIGHT_INDIVIDUAL_IMPROVE * positiveFactorIndividual +
      params.WEIGHT_GLOBAL_IMPROVE * positiveFactorGlobal;

    return { formula, points };
  }
  return { formula: null, points };
};

const formulaUserAVG = (
  params: StrategyParameters,
  taskData: TaskData
): IResponse => {
  // BASIC_POINTS + (TIME_INVESTED_LAST_TASK > USER_AVERAGE ? SMALLER_BONUS : BONUS_FACTOR)

  let points = 0;
  const formula = "FORMULA_USER_AVERAGE_COMPARISON";
  if (
    taskData?.USER_AVERAGE &&
    taskData?.TIME_INVESTED_LAST_TASK &&
    params?.SMALLER_BONUS &&
    params?.BONUS_FACTOR
  ) {
    points =
      params.BASIC_POINTS +
      (taskData.TIME_INVESTED_LAST_TASK > taskData.USER_AVERAGE
        ? params.SMALLER_BONUS
        : params.BONUS_FACTOR);
    return { formula, points };
  }
  return { formula: null, points };
};

const formulaGlobalAVG = (
  params: StrategyParameters,
  taskData: TaskData
): IResponse => {
  // BASIC_POINTS + (TIME_INVESTED_LAST_TASK > GLOBAL_AVERAGE ? SMALLER_BONUS : BONUS_FACTOR)

  let points = 0;
  const formula = "FORMULA_GLOBAL_AVERAGE_COMPARISON";
  if (
    taskData?.GLOBAL_AVERAGE &&
    taskData?.TIME_INVESTED_LAST_TASK &&
    params?.SMALLER_BONUS &&
    params?.BONUS_FACTOR
  ) {
    points =
      params.BASIC_POINTS +
      (taskData.TIME_INVESTED_LAST_TASK > taskData.GLOBAL_AVERAGE
        ? params.SMALLER_BONUS
        : params.BONUS_FACTOR);

    return { formula, points };
  }
  return { formula: null, points };
};

const formulaBasicPoints = (
  params: StrategyParameters,
  taskData: TaskData
): IResponse => {
  // BASIC_POINTS
  let points = 0;
  const formula = "FORMULA_BASIC_POINTS";
  if (params?.BASIC_POINTS) {
    points = params.BASIC_POINTS;
    return { formula, points };
  }
  return { formula: null, points };
};

function parseAndComputeFormula(
  formula: string,
  params: StrategyParameters,
  taskData: TaskData
): {
  formula: string | null;
  points: number;
} {
  let points = 0;
  if (formula === "FORMULA_GLOBAL_AND_INDIVIDUAL_IMPROVEMENT") {
    // BASIC_POINTS + WEIGHT_GLOBAL_IMPROVE * max[0, (GLOBAL_AVERAGE - TIME_INVESTED_LAST_TASK)/GLOBAL_AVERAGE] + WEIGHT_INDIVIDUAL_IMPROVE * max[0, (USER_AVERAGE - TIME_INVESTED_LAST_TASK)/USER_AVERAGE]
    return formulaGlobalAndIndividualImprove(params, taskData);
  }
  if (formula === "FORMULA_USER_AVERAGE_COMPARISON") {
    return formulaUserAVG(params, taskData);
  }
  if (formula === "FORMULA_GLOBAL_AVERAGE_COMPARISON") {
    return formulaGlobalAVG(params, taskData);
  }
  if (formula === "FORMULA_BASIC_POINTS") {
    return formulaBasicPoints(params, taskData);
  }
  return { formula: null, points };
}

export { parseAndComputeFormula, TaskData, calculateAverage };
