import { Model, DataTypes, Sequelize, UUIDV4 } from "sequelize";
import sequelize from "../database"; // Asegúrate de que este importe apunte a tu archivo de configuración de Sequelize
import { Strategy } from "./StrategyModel"; // Importar el modelo de Strategy si es necesario

interface GameAttributes {
  id: string;
  timestampEnd: Date;
  timestampStart: Date;
  currentStrategyId?: string;
  strategy?: Strategy;
  description?: string;
  createdBy: string;
  createdAt?: Date;
}

class Game extends Model<GameAttributes> implements GameAttributes {
  public id!: string;
  public timestampEnd!: Date;
  public timestampStart!: Date;
  public strategy?: Strategy;
  public description?: string;
  public createdBy!: string;
  public createdAt!: Date;
}

Game.init(
  {
    id: {
      type: DataTypes.STRING,
      primaryKey: true,
    },
    timestampEnd: {
      type: DataTypes.DATE,
    },
    timestampStart: {
      type: DataTypes.DATE,
      defaultValue: Sequelize.fn("NOW"),
    },
    description: {
      type: DataTypes.STRING,
    },
    createdBy: {
      type: DataTypes.STRING,
      allowNull: false,
    },
    createdAt: {
      type: DataTypes.DATE,
      defaultValue: Sequelize.fn("NOW"),
    },
  },
  {
    sequelize,
    modelName: "Game",
  }
);

export { Game };
