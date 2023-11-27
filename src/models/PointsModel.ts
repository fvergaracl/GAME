// src/models/PointsModel.ts
import { Model, DataTypes } from "sequelize";
import sequelize from "../database";

interface PointsAttributes {
  id: string;
  points: number;
  formula: string;
  taskUserId: string | null;
  gameUserId: string | null;
}

class Points extends Model<PointsAttributes> implements PointsAttributes {
  public id!: string;
  public points!: number;
  public formula!: string;
  public taskUserId!: string | null;
  public gameUserId!: string | null;
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
      allowNull: true,
      references: { model: "TaskUsers", key: "id" }, // Referencia a la tabla TaskUsers
      unique: true, // Asegura que cada TaskUser esté asociado a un solo Points
    },
    gameUserId: {
      type: DataTypes.UUID,
      allowNull: true,
      references: { model: "GameUsers", key: "id" },
    },
  },
  {
    sequelize,
    modelName: "Points",
    updatedAt: false,
    hooks: {
      beforeValidate: (points, options) => {
        if (
          (points.taskUserId && points.gameUserId) ||
          (!points.taskUserId && !points.gameUserId)
        ) {
          throw new Error(
            "You must provide either a taskUserId or a gameUserId"
          );
        }
      },
    },
  }
);

export { Points };
