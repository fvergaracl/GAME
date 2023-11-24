// src/models/TaskModel.ts
import { Model, DataTypes } from "sequelize";
import sequelize from "../database";
import { Game } from "./GameModel"; // Importa el modelo de Game

interface TaskAttributes {
  id: string;
  name: string;
  description?: string;
  gameId?: string; 
  createdBy: string;
  createdAt?: Date;
}

class Task extends Model<TaskAttributes> implements TaskAttributes {
  public id!: string;
  public name!: string;
  public description?: string;
  public createdBy!: string;
  public createdAt!: Date;
}

Task.init(
  {
    id: {
      type: DataTypes.STRING,
      primaryKey: true,
      defaultValue: DataTypes.UUIDV4, // Usando UUID para el ID de la tarea
    },
    name: {
      type: DataTypes.STRING,
      allowNull: false,
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
      defaultValue: DataTypes.NOW,
    },
  },
  {
    sequelize,
    modelName: "Task",
  }
);

export { Task };
