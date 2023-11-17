const calculateGlobalBehaviorTime = (game: any): number => {
  // Example implementation to calculate the average time between tasks across all users for a game
  // This assumes that 'game' has a property 'userTasks' which is a map/object with userIds as keys and arrays of task completion timestamps as values

  let totalTimeInterval = 0;
  let countIntervals = 0;

  for (const userId in game.userTasks) {
    if (game.userTasks[userId].length < 2) {
      continue; // Skip users with less than two tasks
    }

    for (let i = 1; i < game.userTasks[userId].length; i++) {
      // Calculate the time interval for each user
      const timeDiff =
        game.userTasks[userId][i].timestamp -
        game.userTasks[userId][i - 1].timestamp;
      totalTimeInterval += timeDiff;
      countIntervals++;
    }
  }

  if (countIntervals === 0) {
    return 0; // No intervals to calculate an average
  }

  // Return the global average time interval in milliseconds
  return totalTimeInterval / countIntervals;
};

export { calculateGlobalBehaviorTime };
