// src/models/UserModel.ts
import { Model, DataTypes } from "sequelize";
import sequelize from "../database"; // Asegúrate de que este importe apunte a tu archivo de configuración de Sequelize

interface UserAttributes {
  userId: string; // ID manejado por un usuario externo
}

class User extends Model<UserAttributes> implements UserAttributes {
  public userId!: string;
}

User.init(
  {
    userId: {
      type: DataTypes.STRING,
      primaryKey: true,
      allowNull: false, // Asegurando que userId sea siempre proporcionado
    },
  },
  {
    sequelize,
    modelName: "Users",
    updatedAt: false, // Evitando que se cree el campo "updatedAt"
  }
);

export { User };
  