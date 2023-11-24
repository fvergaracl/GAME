import { Model, DataTypes, Sequelize, UUIDV4 } from "sequelize";
import sequelize from "../database"; // Asegúrate de que este importe apunte a tu archivo de configuración de Sequelize
import { Game } from "./GameModel"; // Importar el modelo de Game si es necesario

// Definición de las interfaces
interface CaseSub {
  criteria: string;
  formula: string;
}

interface Case {
  criteria: string;
  formula: string;
  subCases?: CaseSub[];
}

interface StrategyParameters {
  BASIC_POINTS: number;
  BONUS_FACTOR?: number;
  SMALLER_BONUS?: number;
  INDIVIDUAL_IMPROVEMENT_FACTOR?: number;
  WEIGHT_GLOBAL_IMPROVE?: number;
  WEIGHT_INDIVIDUAL_IMPROVE?: number;
}

interface StrategyAttributes {
  id?: string;
  name: string;
  description: string;
  strategyType: string;
  parameters: StrategyParameters;
  cases: Case[];
}

// Modelo Strategy
class Strategy extends Model<StrategyAttributes> implements StrategyAttributes {
  public id!: string;
  public name!: string;
  public description!: string;
  public strategyType!: string;
  public parameters!: StrategyParameters;
  public cases!: Case[];
}

Strategy.init(
  {
    id: {
      type: DataTypes.STRING,
      primaryKey: true,
    },
    name: {
      type: DataTypes.STRING,
      allowNull: false,
    },
    description: {
      type: DataTypes.STRING,
      allowNull: false,
    },
    strategyType: {
      type: DataTypes.STRING,
      allowNull: false,
    },
    parameters: {
      type: DataTypes.JSON,
      allowNull: false,
    },
    cases: {
      type: DataTypes.JSON,
      allowNull: false,
    },
  },
  {
    sequelize,
    modelName: "Strategy",
  }
);

export { Strategy };
