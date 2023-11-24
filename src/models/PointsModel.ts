// src/models/PointsModel.ts
import { Model, DataTypes } from "sequelize";
import sequelize from "../database";
import { TaskUser } from "./TaskUserModel";

interface PointsAttributes {
  id: string; // ID único
  points: number; // Puntos
  formula: string; // Fórmula utilizada para calcular los puntos
  taskUserId: string; // Clave foránea a TaskUser
}

class Points extends Model<PointsAttributes> implements PointsAttributes {
  public id!: string;
  public points!: number;
  public formula!: string;
  public taskUserId!: string;
}

Points.init(
  {
    id: {
      type: DataTypes.UUID,
      primaryKey: true,
      defaultValue: DataTypes.UUIDV4,
    },
    points: {
      type: DataTypes.INTEGER,
      allowNull: false,
    },
    formula: {
      type: DataTypes.STRING,
      allowNull: false,
    },
    taskUserId: {
      type: DataTypes.UUID,
      allowNull: false,
      references: { model: "TaskUsers", key: "id" }, // Referencia a la tabla TaskUsers
      unique: true, // Asegura que cada TaskUser esté asociado a un solo Points
    },
  },
  {
    sequelize,
    modelName: "Points",
    updatedAt: false,
  }
);

export { Points };
