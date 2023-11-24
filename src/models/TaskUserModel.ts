// src/models/TaskUserModel.ts
import { Model, DataTypes } from "sequelize";
import sequelize from "../database";
import { Task } from "./TaskModel";
import { User } from "./UserModel";

interface TaskUserAttributes {
  id: string; // ID único
  timestamp: Date; // Timestamp de la asociación
  taskId: string; // Clave foránea a Task
  userId: string; // Clave foránea a User
}

class TaskUser extends Model<TaskUserAttributes> implements TaskUserAttributes {
  public id!: string;
  public timestamp!: Date;
  public taskId!: string;
  public userId!: string;
}

TaskUser.init(
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
    taskId: {
      type: DataTypes.STRING,
      references: { model: "Tasks", key: "id" },
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
    modelName: "TaskUser",
    updatedAt: false,
  }
);

// Definiendo las relaciones
Task.belongsToMany(User, { through: TaskUser, foreignKey: "taskId" });
User.belongsToMany(Task, { through: TaskUser, foreignKey: "userId" });

export { TaskUser };
