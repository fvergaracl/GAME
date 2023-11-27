import { Model, DataTypes, Sequelize, UUIDV4 } from "sequelize";
import sequelize from "../database"; // Asegúrate de que este importe apunte a tu archivo de configuración de Sequelize
import { Strategy } from "./StrategyModel"; // Importar el modelo de Strategy si es necesario

interface GameBase {
  startDateTime?: Date;
  gameId?: string;
  endDateTime?: Date | undefined;
  description?: string | undefined;
}

interface CreateGameBody extends GameBase {
  currentStrategyId: string;
  gameId: string;
}

interface GameAttributes extends GameBase {
  id?: string;
  gameId?: string;
  strategy?: Strategy;
  createdBy?: string;
  createdAt?: Date;
  currentStrategyId: string;
  description?: string | undefined;
  startDateTime?: Date;
  endDateTime?: Date | undefined;
}

class Game extends Model<GameAttributes> implements GameAttributes {
  public id!: string;
  public gameId?: string;
  public startDateTime?: Date;
  public endDateTime?: Date | undefined;
  public strategy?: Strategy;
  public description?: string | undefined;
  public createdBy?: string;
  public createdAt!: Date;
  public currentStrategyId!: string;
}

Game.init(
  {
    id: {
      type: DataTypes.STRING,
      primaryKey: true,
      defaultValue: UUIDV4,
    },
    gameId: {
      type: DataTypes.STRING,
      unique: true,
    },
    endDateTime: {
      type: DataTypes.DATE,
      allowNull: true,
    },
    startDateTime: {
      type: DataTypes.DATE,
      defaultValue: Sequelize.fn("NOW"),
    },
    description: {
      type: DataTypes.STRING,
      allowNull: true,
    },
    createdBy: {
      type: DataTypes.STRING,
      allowNull: false,
      defaultValue: "system",
    },
    createdAt: {
      type: DataTypes.DATE,
      defaultValue: Sequelize.fn("NOW"),
    },
    currentStrategyId: {
      type: DataTypes.STRING,
      allowNull: false,
    },
  },
  {
    sequelize,
    modelName: "Game",
   
  }
);

export { Game, CreateGameBody, GameAttributes };
