### Cases and Points Awarded Table:

| Case/Subcase | Conditions                                                              | Points Awarded                                                                                                                   |
| ------------ | ----------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| Case 1       | First/second measurement without any prior users having 2 measurements. | Basic initial points (`defaut_points_task_campaign`).                                                                            |
| Case 2.1     | Second measurement with time taken > global calculation.                | Fixed points or bonus/penalty based on the difference from the global calculation.                                               |
| Case 2.2     | Second measurement with time taken < global calculation.                | Base points + bonus.                                                                                                             |
| Case 3       | Comparison with individual calculation (greater or lesser).             | Base + bonus/penalty.                                                                                                            |
| Case 4.1     | Individual improvement but below the global average.                    | `10 + 10*(individual_improvement) + 0 = Adjusted points based on individual improvement without penalty for global performance.` |
| Case 4.2     | Individual worsening and below the global average.                      | `10 + 0 + 0 = 10 (Default points).`                                                                                              |
| Case 4.3     | Individual improvement and above the global average.                    | `10 + 10*(individual_improvement) + 10*(global_improvement) = Significantly increased points.`                                   |
| Case 4.4     | Individual worsening, but above the global average.                     | `10 + 0 + 10*(global_improvement) = Adjusted points based on global performance.`                                                |
