/* eslint-disable @typescript-eslint/require-await */
import { app } from "./app";
import sequelize from "./database";
import { Strategy, Game, Task, User, TaskUser, Points } from "./models"; // Importación de los modelos
import * as dotenv from "dotenv";
dotenv.config();

const PORT = process.env["PORT"] ? parseInt(process.env["PORT"], 10) : 3000;

sequelize
  .authenticate()
  .then(() => {
    console.log(
      "Connection to the PostgreSQL database has been established successfully."
    );
    Strategy.hasMany(Game, { foreignKey: "currentStrategyId" });
    Game.belongsTo(Strategy, { foreignKey: "currentStrategyId" });
    // GAME HAVE MANY TASKS OR 0
    // TAKK BELONGS TO GAME OBLIGATORY
    Game.hasMany(Task, { foreignKey: "gameId" });
    Task.belongsTo(Game, { foreignKey: "gameId" });

    Task.belongsToMany(User, { through: TaskUser, foreignKey: "taskId" });
    User.belongsToMany(Task, { through: TaskUser, foreignKey: "userId" });

    // Relación con TaskUser
    Points.belongsTo(TaskUser, { foreignKey: "taskUserId", as: "taskUser" });
    TaskUser.hasOne(Points, { foreignKey: "taskUserId", as: "points" });

    Strategy.sync();
    Game.sync();
    Task.sync();
    User.sync();
    TaskUser.sync();
    Points.sync();
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
