// src/models/ApiKeyModel.ts
import { Model, DataTypes } from "sequelize";
import sequelize from "../database"; // Asegúrate de que este importe apunte a tu archivo de configuración de Sequelize

interface ApiKeyAttributes {
  id: string;
  key: string;
  toolName: string;
  expirationDate?: Date; // Opcional
}

class ApiKey extends Model<ApiKeyAttributes> implements ApiKeyAttributes {
  public id!: string;
  public key!: string;
  public toolName!: string;
  public expirationDate?: Date;
}

ApiKey.init(
  {
    id: {
      type: DataTypes.UUID,
      primaryKey: true,
      defaultValue: DataTypes.UUIDV4,
    },
    key: {
      type: DataTypes.STRING,
      allowNull: false,
      unique: true,
    },
    toolName: {
      type: DataTypes.STRING,
      allowNull: false,
    },
    expirationDate: {
      type: DataTypes.DATE,
      allowNull: true, // Permite que el campo sea opcional
    },
  },
  {
    sequelize,
    modelName: "ApiKey",
    updatedAt: false,
  }
);

export { ApiKey };
