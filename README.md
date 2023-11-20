# GAME (Goals And Motivation Engine)

## Overview

This Gamification Engine API is a Node.js application using Express and TypeScript. It's designed to provide a robust backend for gamification features, integrating MongoDB for data persistence.

## Prerequisites

- Node.js >= 15.0.0
- npm (Node Package Manager)
- MongoDB

## Installation

1. **Clone the repository**

   ```
   git clone [REPO-URL-WIP]
   cd [REPONAME-WIP]
   ```

2. **Install dependencies**

   ```
   npm install
   ```

3. **Install TypeScript globally (Optional)**
   ```
   npm install -g typescript
   ```

# How to define your stategy

### Constants for Criteria

| Name                        | Description                                                      | Type    | Condition Used                      | Mandatory |
| --------------------------- | ---------------------------------------------------------------- | ------- | ----------------------------------- | --------- |
| EARLY_TASK_NO_GLOBAL        | Identifies early tasks of a user without global data.            | Boolean | `numberOfTasks <= 2 && !globalData` | Yes       |
| SECOND_TASK_GLOBAL_DATA     | Indicates the second task of a user with global data.            | Boolean | `numberOfTasks == 2 && globalData`  | Yes       |
| INDIVIDUAL_DATA_NO_GLOBAL   | Scenario where individual data is available, but no global data. | Boolean | `individualData && !globalData`     | Yes       |
| BOTH_INDIVIDUAL_GLOBAL_DATA | Applies when both individual and global data are available.      | Boolean | `individualData && globalData`      | Yes       |

### Criteria Variables

| Name                    | Description                                          | Used As Criterion |
| ----------------------- | ---------------------------------------------------- | ----------------- |
| TIME_INVESTED_LAST_TASK | The time a user invested in their last task.         | Yes               |
| GLOBAL_AVERAGE          | The average time invested in tasks across all users. | Yes               |

### Constants for Point Calculation Formulas

| Name                          | Description                                                     | Type   | Mandatory |
| ----------------------------- | --------------------------------------------------------------- | ------ | --------- |
| BASIC_POINTS                  | Base points awarded for tasks.                                  | Number | Yes       |
| BONUS_FACTOR                  | Additional points for better performance than global average.   | Number | No        |
| SMALLER_BONUS                 | Smaller bonus points for performance worse than global average. | Number | No        |
| INDIVIDUAL_IMPROVEMENT_FACTOR | Factor to enhance points based on individual improvement.       | Number | No        |
| WEIGHT_GLOBAL_IMPROVE         | Weight for improvement relative to global average.              | Number | No        |
| WEIGHT_INDIVIDUAL_IMPROVE     | Weight for improvement relative to individual average.          | Number | No        |

### Additional Considerations

| Name                                | Description                                             | Type   | Mandatory |
| ----------------------------------- | ------------------------------------------------------- | ------ | --------- |
| BONUS_FACTOR_VALUE                  | The constant value for `bonus_factor`.                  | Number | Yes       |
| SMALLER_BONUS_VALUE                 | The constant value for `smaller_bonus`.                 | Number | Yes       |
| INDIVIDUAL_IMPROVEMENT_FACTOR_VALUE | The constant value for `individual_improvement_factor`. | Number | Yes       |
| WEIGHT_GLOBAL_IMPROVE_VALUE         | The constant value for `weight_global_improve`.         | Number | Yes       |
| WEIGHT_INDIVIDUAL_IMPROVE_VALUE     | The constant value for `weight_individual_improve`.     | Number | Yes       |


## Setting up the Project

- **TypeScript Configuration**:

  - Run `tsc --init` to create a `tsconfig.json` file.
  - Customize this file as per your project needs.

- **Directory Structure**:
  - `src`: Main source code.
    - `index.ts`: Entry point of the application.
    - `app.ts`: Express app configuration.
    - `routes`: Contains route definitions.
    - `controllers`: Business logic.
    - `models`: MongoDB models.
    - `config`: Configuration files.

## Running the Application

- **Compile TypeScript to JavaScript**

  ```
  tsc
  ```

  Or, if TypeScript is installed locally:

  ```
  npm run build
  ```

- **Start the server**
  ```
  npm start
  ```

## Testing

- Test your endpoints using tools like Postman or any HTTP client.

## Development Notes

- Ensure Node.js and npm are correctly installed.
- For any changes in the configuration or dependencies, restart the server to reflect changes.
- Maintain a modular and clear structure for scalability and easy maintenance.

## Contributing

Contributions to this project are welcome. Please fork the repository and submit a pull request.

## License

This project is licensed under the [MIT License](LICENSE).
