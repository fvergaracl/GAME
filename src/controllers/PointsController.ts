import { Request, Response } from "express";
import {
  PointsModel,
  TaskModel,
  Task,
  Points,
  StrategyModel,
  Strategy,
  GameModel,
  UserModel,
  Game,
  StrategyParameters,
} from "../models";

import {
  parseAndComputeFormula,
  TaskData,
  calculateAverage,
} from "../utils/parseAndComputeFormula";

class PointsController {
  /*
  router.get("/:userId", PointsController.getUserPoints);
router.get("/:userId/:taskId", PointsController.getUserPointsInTask);
router.get("/:userId/:gameId", PointsController.getUserPointsInGame);
  */

  static async getUserPoints(req: Request, res: Response) {
    try {
      res.status(200).json({ message: "getUserPoints" });
    } catch (error) {
      res.status(500).json({ message: "getUserPoints -ERROR" });
    }
  }

  static async getUserPointsInTask(req: Request, res: Response) {
    try {
      res.status(200).json({ message: "getUserPointsInTask" });
    } catch (error) {
      res.status(500).json({ message: "getUserPointsInTask -ERROR" });
    }
  }

  static async getUserPointsInGame(req: Request, res: Response) {
    try {
      res.status(200).json({ message: "getUserPointsInGame" });
    } catch (error) {
      res.status(500).json({ message: "getUserPointsInGame -ERROR" });
    }
  }

  static async assignPointsToUser(req: Request, res: Response) {
    try {
      const body = req.body as Points;
      const { idGame, idTask } = body;
      let idUser = body?.idUser;
      // Check if idGame exists
      let game = await GameModel.findById(idGame);
      console.log({ game });
      if (!game) {
        return res.status(404).json({ message: "Game not found" });
      }

      if (idTask) {
        // Check if idTask exists
        let task = await TaskModel.findById(idTask);
        if (!task) {
          return res.status(404).json({ message: "Task not found" });
        }
      }

      // Check if idUser exists and create if not exists
      let userIsCreated = undefined;
      let user;
      console.log("-122");
      console.log({ idUser });
      if (idUser) {
        user = await UserModel.findOne({ userId: idUser });
      }
      console.log("-1");
      if (!user || !idUser) {
        console.log("------------------------------------------------------");
        const newUser = new UserModel({ userId: idUser });
        user = await newUser.save();
        userIsCreated = true;
      }

      const allActionsUsers = await UserModel.find({}).select("actions");
      const allActions = allActionsUsers.map((user) => user.actions);

      const userActions = user?.actions;
      let TIME_INVESTED_LAST_TASK = undefined;
      let GLOBAL_AVERAGE = undefined;
      let USER_AVERAGE = undefined;

      if (userActions && userActions.length > 2) {
        // get difference between last action and previous action
        const lastAction = userActions[userActions.length - 1];
        const previousAction = userActions[userActions.length - 2];
        const difference = lastAction.timestamp - previousAction.timestamp;
        const differenceInMinutes = difference / 60000;
        TIME_INVESTED_LAST_TASK = differenceInMinutes;
      }
      // if allActions is an array of arrays

      if (allActions && allActions.length > 0) {
        const allActionsFlat = allActions.flat();
        const allActionsTimestamps =
          allActionsFlat
            .map((action) => action?.timestamp)
            .filter(
              (timestamp): timestamp is number => typeof timestamp === "number"
            ) || [];

        let average = undefined;
        if (allActionsTimestamps.length > 0) {
          average = calculateAverage(allActionsTimestamps);
          GLOBAL_AVERAGE = average;
        }
        GLOBAL_AVERAGE = average;
      }

      if (userActions && userActions.length > 0) {
        const userActionsTimestamps = userActions.map(
          (action) => action?.timestamp
        );
        let average = undefined;
        if (userActionsTimestamps && userActionsTimestamps.length > 0) {
          average = calculateAverage(userActionsTimestamps);
          USER_AVERAGE = average;
        }
        USER_AVERAGE = average;
      }

      const taskData: TaskData = {
        TIME_INVESTED_LAST_TASK,
        GLOBAL_AVERAGE,
        USER_AVERAGE,
      };

      const gameStrategyParams = game?.strategy?.parameters;
      if (!gameStrategyParams) {
        return res.status(404).json({ message: "Strategy not found" });
      }
      const cases = game?.strategy?.cases;
      // calculate all classes
      const allClasses = cases?.map((caseItem) =>
        parseAndComputeFormula(caseItem.formula, gameStrategyParams, taskData)
      );
      // get max points and formula
      const maxPoints = allClasses
        ?.map((item) => {
          if (item?.points) {
            return item.points;
          }
          return 0;
        })
        .reduce((a, b) => Math.max(a, b));
        
      // const maxPoints = allClasses
      //   ?.map((item) => {
      //     if (item?.points) {
      //       return item.points;
      //     }
      //     return 0;
      //   })
      //   .reduce((a, b) => Math.max(a, b));
      console.log("maxPoints", maxPoints);
      console.log("==================================");
      res
        .status(200)
        .json({ message: "assignPointsToUser", maxPoints, allClasses });
    } catch (error) {
      res.status(500).send(error);
    }
  }
}

export { PointsController };
