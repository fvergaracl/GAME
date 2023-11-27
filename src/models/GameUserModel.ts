// src/models/TaskUserModel.ts
import { Model, DataTypes } from "sequelize";
import sequelize from "../database";

interface GameUserAttributes {
  id: string; // ID único
  timestamp: Date; // Timestamp de la asociación
  gameId: string; // Clave foránea a Task
  userId: string; // Clave foránea a User
}

class GameUser extends Model<GameUserAttributes> implements GameUserAttributes {
  public id!: string;
  public timestamp!: Date;
  public gameId!: string;
  public userId!: string;
}

GameUser.init(
  {
    id: {
      type: DataTypes.UUID,
      primaryKey: true,
      defaultValue: DataTypes.UUIDV4,
    },
    timestamp: {
      type: DataTypes.DATE,
      defaultValue: DataTypes.NOW,
    },
    gameId: {
      type: DataTypes.STRING,
      references: { model: "Game", key: "id" },
      allowNull: false,
    },
    userId: {
      type: DataTypes.STRING,
      references: { model: "Users", key: "userId" },
      allowNull: false,
    },
  },
  {
    sequelize,
    modelName: "GameUser",
    updatedAt: false,
  }
);

export { GameUser };
