/* eslint-disable @typescript-eslint/require-await */
import { app } from "./app";
import sequelize from "./database";
import {
  Strategy,
  Game,
  Task,
  User,
  TaskUser,
  Points,
  GameUser,
} from "./models";
import * as dotenv from "dotenv";
import { initDefaultStrategy } from "./services/initDefaultStrategy";
dotenv.config();

const PORT = process.env["PORT"] ? parseInt(process.env["PORT"], 10) : 3000;

sequelize
  .authenticate()
  .then(async () => {
    console.log(
      "Connection to the PostgreSQL database has been established successfully."
    );
    Strategy.hasMany(Game, { foreignKey: "currentStrategyId" });
    Game.belongsTo(Strategy, { foreignKey: "currentStrategyId" });

    Game.hasMany(Task, { foreignKey: "gameId" });
    Task.belongsTo(Game, { foreignKey: "gameId" });

    Task.belongsToMany(User, { through: TaskUser, foreignKey: "taskId" });
    Game.belongsToMany(User, { through: GameUser, foreignKey: "gameId" });
    User.belongsToMany(Task, { through: TaskUser, foreignKey: "userId" });

    Points.belongsTo(TaskUser, { foreignKey: "taskUserId", as: "taskUser" });
    Points.belongsTo(GameUser, { foreignKey: "gameUserId", as: "gameUser" });
    TaskUser.hasOne(Points, { foreignKey: "taskUserId", as: "points" });
    GameUser.hasOne(Points, { foreignKey: "gameUserId", as: "points" });

    await Strategy.sync({ force: true });
    await Game.sync({ force: true });
    await Task.sync({ force: true });
    await User.sync({ force: true });
    await TaskUser.sync({ force: true });
    await GameUser.sync({ force: true });
    await Points.sync({ force: true });
    await initDefaultStrategy();
  })
  .then(() => {
    // Sincronizar los modelos con la base de datos
    return sequelize.sync();
  })
  .then(() => {
    // Iniciar el servidor una vez que todos los modelos estén sincronizados
    app.listen(PORT, () => {
      console.log("-".repeat(32));
      console.log(`|Server listening on port ${PORT} |`);
      console.log("-".repeat(32));
    });
  })
  .catch((error) => {
    console.error(
      "Unable to connect to the database or start the server:",
      error
    );
  });
