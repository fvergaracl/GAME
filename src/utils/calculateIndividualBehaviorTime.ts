const calculateIndividualBehaviorTime = (user: any): number => {
  // This assumes that 'user' has a property 'tasks' which is an array of task completion timestamps
  if (!user.tasks || user.tasks.length < 2) {
    // If there are less than two tasks, we cannot calculate an average time
    return 0;
  }

  let totalTimeInterval = 0;
  for (let i = 1; i < user.tasks.length; i++) {
    // Calculate the time interval between each consecutive tasks
    const timeDiff = user.tasks[i].timestamp - user.tasks[i - 1].timestamp;
    totalTimeInterval += timeDiff;
  }

  // Return the average time interval in milliseconds
  return totalTimeInterval / (user.tasks.length - 1);
};

export { calculateIndividualBehaviorTime };
