

## Gamification Point Calculation Strategy 

### 1. 🚀 Basic Point Calculation (For Early Tasks without Global Data)
- **Formula**: 
  $$ \text{points\_awarded} = \text{default\_points\_task\_campaign} $$
- **Explanation**: Awards a basic number of points (\( \text{default\_points\_task\_campaign} \)) for the first or second task when there's no global data available.

### 2. 🌍 Second Task with Global Data
- **Formula**: 
  - If \( \text{time\_invested\_last\_task} \leq \text{global\_average} \): 
    $$ \text{points\_awarded} = \text{default\_points\_task\_campaign} + \text{bonus\_factor} $$
  - If \( \text{time\_invested\_last\_task} > \text{global\_average} \): 
    $$ \text{points\_awarded} = \text{default\_points\_task\_campaign} + \text{smaller\_bonus} $$
- **Explanation**: Rewards the user based on their performance compared to the global average. A higher bonus for better performance and a smaller bonus otherwise.

### 3. 🌟 With Individual Data but No Global Data
- **Formula**: 
  $$ \text{points\_awarded} = \text{default\_points\_task\_campaign} + (\text{individual\_improvement\_factor} \times \text{individual\_performance}) $$
- **Explanation**: Focuses on individual performance. Awards points based on the default setting, enhanced by the individual's improvement over time.

### 4. ⚖️ With Both Individual and Global Data
- **Formula**: 
  $$ \text{points\_awarded} = \text{default\_points\_task\_campaign} + \text{weight\_global\_improve} \times \max(0, (\text{global\_average} - \text{time\_invested\_last\_task})/\text{global\_average}) + \text{weight\_individual\_improve} \times \max(0, (\text{individual\_average} - \text{time\_invested\_last\_task})/\text{individual\_average}) $$
- **Explanation**: This comprehensive formula considers both individual and global performance. Rewards are adjusted based on the last task's time relative to both the global and individual averages.

---

### 💡 Additional Considerations:
- **Bonus Factors**: The `bonus_factor` and `smaller_bonus` are constants or dynamic values that should be defined based on game dynamics and user engagement strategies.
- **Improvement Factors**: `individual_improvement_factor`, `weight_global_improve`, and `weight_individual_improve` are crucial in determining how much a user's performance influences their point gain.

This strategy ensures a positive and encouraging environment by focusing on rewarding rather than penalizing, motivating users to improve their performance while enjoying the gamification experience.
