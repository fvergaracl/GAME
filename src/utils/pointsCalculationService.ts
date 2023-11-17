import { calculateIndividualBehaviorTime } from "./calculateIndividualBehaviorTime";
import { calculateGlobalBehaviorTime } from "./calculateGlobalBehaviorTime";

function defaultPointsTaskCampaign(game: any): number {
  return game.defaultPointsTaskCampaign;
}

const formulaBased = (
  user: any,
  game: any,
  taskCompletionTime: number
): number => {
  // We assume that we have functions that calculate individual and global behavior.
  // These functions must be defined according to your specific rules.
  const individualBehaviorTime = calculateIndividualBehaviorTime(user);
  const globalBehaviorTime = calculateGlobalBehaviorTime(game);

  // We calculate improvement factors based on task completion time.
  const factorIndividual =
    individualBehaviorTime > 0
      ? (individualBehaviorTime - taskCompletionTime) / individualBehaviorTime
      : 0;
  const factorGlobal =
    globalBehaviorTime > 0
      ? (globalBehaviorTime - taskCompletionTime) / globalBehaviorTime
      : 0;

  // We ensure that the factors are not negative.
  const positiveFactorIndividual = Math.max(0, factorIndividual);
  const positiveFactorGlobal = Math.max(0, factorGlobal);

  // We calculate the points based on the formula
  const points =
    game.weightIndividualImprove * positiveFactorIndividual +
    game.weightGlobalImprove * positiveFactorGlobal;

  return points;
};

const formulaBasedMaxBonus = (
  user: any,
  game: any,
  taskCompletionTime: number
): number => {
  // Implementing the formula-based calculation with a maximum bonus limit
  // This example reuses the 'formulaBased' function logic with an additional cap on the bonus

  const basePoints = formulaBased(user, game, taskCompletionTime);
  const maxBonus = 20; // Example maximum bonus limit, adjust as needed

  return Math.min(basePoints, maxBonus); // Ensure the points do not exceed the maximum bonus
};

const defaultPointsTaskCampaignPlusMinorBonus = (
  user: any,
  game: any,
  taskCompletionTime: number
): number => {
  // Implement logic to calculate default points with an additional minor bonus
  // Example: default points for completing a task plus a small additional bonus

  const defaultPoints = game.defaultPointsTaskCampaign;
  const minorBonus = game.minorBonus; 

  // You might want to add logic here that determines the bonus based on taskCompletionTime or other factors

  return defaultPoints + minorBonus; // Sum of default points and minor bonus
};

export {
  defaultPointsTaskCampaign,
  formulaBased,
  formulaBasedMaxBonus,
  defaultPointsTaskCampaignPlusMinorBonus,
};
