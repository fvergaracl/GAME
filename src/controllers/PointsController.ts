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
  static async getUserPoints(req: Request, res: Response) {
    try {
      const { userId } = req.params;
      const { from, to } = req.query;
      if (from && isNaN(new Date(String(from)).getTime())) {
        return res.status(400).json({ message: "'from' is invalid" });
      }
      if (to && isNaN(new Date(String(to)).getTime())) {
        return res.status(400).json({ message: "'to' is invalid" });
      }

      if (!userId) {
        return res.status(400).json({ message: "idUser is required" });
      }

      const userData = await UserModel.findOne({ userId });
      if (!userData) {
        return res
          .status(404)
          .json({ message: "User doesn't exist", points: 0 });
      }
      const userActions = userData.actions;
      if (!userActions) {
        return res
          .status(404)
          .json({ message: "User doesn't have actions", points: 0 });
      }

      let query = { userId };
      if (from) {
        query = {
          ...query,
          createdAt: { $gte: new Date(String(from)) },
        } as any;
      }
      if (to) {
        query = { ...query, createdAt: { $lte: new Date(String(to)) } } as any;
      }
      if (from && to) {
        query = {
          ...query,
          createdAt: {
            $gte: new Date(String(from)),
            $lte: new Date(String(to)),
          },
        } as any;
      }

      console.log({ query });

      const usersPoints = await PointsModel.find(query);
      if (!usersPoints) {
        return res
          .status(404)
          .json({ message: "User doesn't have points", points: 0 });
      }
      const points = usersPoints.reduce((a, b) => a + (b?.points ?? 0), 0);
      res.status(200).json({
        message: "Sum of points",
        points,
      });
    } catch (error) {
      res.status(500).json({ message: error, points: -1 });
    }
  }

  static async getUserPointsInTask(req: Request, res: Response) {
    try {
      // /points/:userId/:idTask
      // with from /points/:userId/:idTask?from=2021-05-01T00:00:00.000Z
      // with to /points/:userId/:idTask?to=2021-05-01T00:00:00.000Z
      // with from and to /points/:userId/:idTask?from=2021-05-01T00:00:00.000Z&to=2021-05-01T00:00:00.000Z
      const { userId, idTask } = req.params;
      const { from, to } = req.query;
      if (from && isNaN(new Date(String(from)).getTime())) {
        return res.status(400).json({ message: "'from' is invalid" });
      }
      if (to && isNaN(new Date(String(to)).getTime())) {
        return res.status(400).json({ message: "'to' is invalid" });
      }
      if (!userId) {
        return res.status(400).json({ message: "idUser is required" });
      }
      if (!idTask) {
        return res.status(404).json({ message: "idTask not found" });
      }

      const userData = await UserModel.findOne({ userId });
      if (!userData) {
        return res
          .status(404)
          .json({ message: "User doesn't exist", points: 0 });
      }
      const userActions = userData.actions;
      if (!userActions) {
        return res
          .status(404)
          .json({ message: "User doesn't have actions", points: 0 });
      }

      let query = {
        userId,
        "task._id": idTask,
      };

      if (from) {
        query = {
          ...query,
          createdAt: { $gte: new Date(String(from)) },
        } as any;
      }
      if (to) {
        query = { ...query, createdAt: { $lte: new Date(String(to)) } } as any;
      }
      if (from && to) {
        query = {
          ...query,
          createdAt: {
            $gte: new Date(String(from)),
            $lte: new Date(String(to)),
          },
        } as any;
      }

      const usersTaskPoints = await PointsModel.find(query);
      if (!usersTaskPoints) {
        return res.status(404).json({
          message: "User doesn't have points in this task",
          points: 0,
        });
      }
      const points = usersTaskPoints.reduce((a, b) => a + (b?.points ?? 0), 0);
      res.status(200).json({
        message: "Sum of points in task",
        points,
      });
    } catch (error) {
      res.status(500).json({ message: error, points: -1 });
    }
  }

  static async getUserPointsInGame(req: Request, res: Response) {
    try {
      const { userId, idGame } = req.params;
      const { from, to } = req.query;
      if (from && isNaN(new Date(String(from)).getTime())) {
        return res.status(400).json({ message: "'from' is invalid" });
      }
      if (to && isNaN(new Date(String(to)).getTime())) {
        return res.status(400).json({ message: "'to' is invalid" });
      }

      if (!userId) {
        return res.status(400).json({ message: "idUser is required" });
      }
      if (!idGame) {
        return res.status(404).json({ message: "idGame not found" });
      }

      const userData = await UserModel.findOne({ userId });
      if (!userData) {
        return res
          .status(404)
          .json({ message: "User doesn't exist", points: 0 });
      }
      const userActions = userData.actions;
      if (!userActions) {
        return res
          .status(404)
          .json({ message: "User doesn't have actions", points: 0 });
      }

      let query = {
        userId,
        "game._id": idGame,
      };

      if (from) {
        query = {
          ...query,
          createdAt: { $gte: new Date(String(from)) },
        } as any;
      }
      if (to) {
        query = { ...query, createdAt: { $lte: new Date(String(to)) } } as any;
      }
      if (from && to) {
        query = {
          ...query,
          createdAt: {
            $gte: new Date(String(from)),
            $lte: new Date(String(to)),
          },
        } as any;
      }

      const usersGamePoints = await PointsModel.find(query);
      if (!usersGamePoints) {
        return res.status(404).json({
          message: "User doesn't have points in this game",
          points: 0,
        });
      }
      const points = usersGamePoints.reduce((a, b) => a + (b?.points ?? 0), 0);
      res.status(200).json({
        message: "Sum of points in game",
        points,
      });
    } catch (error) {
      res.status(500).json({ message: error, points: -1 });
    }
  }

  static async assignPointsToUser(req: Request, res: Response) {
    try {
      const body = req.body as Points;
      const { userId } = body;
      const { idGame, idTask } = req.params;
      let task;
      if (!userId) {
        return res.status(400).json({ message: "idUser is required" });
      }
      if (!idGame) {
        return res.status(404).json({ message: "Game not found" });
      }

      let game = await GameModel.findById(idGame);
      if (!game) {
        return res.status(404).json({ message: "Game not found" });
      }

      if (idTask) {
        // Check if idTask exists
        task = await TaskModel.findById(idTask);
        if (!task) {
          return res.status(404).json({ message: "Task not found" });
        }
        if (task?.game?._id.toString() !== idGame) {
          return res.status(404).json({ message: "Task is not in this game" });
        }
      }

      // Check if idUser exists and create if not exists
      let userIsCreated = undefined;
      let user;
      if (userId) {
        user = await UserModel.findOne({ userId: userId });
      }

      if (!user) {
        const newUser = new UserModel({ userId: userId });
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
      const allCasesPoints = cases?.map((caseItem) =>
        parseAndComputeFormula(caseItem.formula, gameStrategyParams, taskData)
      );
      // get max points and formula
      const pointsAssigned = allCasesPoints?.reduce((a, b) =>
        a.points > b.points ? a : b
      );

      const points = pointsAssigned?.points ?? 0;
      const formula = pointsAssigned?.formula ?? "No formula";
      if (points < 0) {
        // negative points because the formula's strategy is not correct
        return res.status(400).json({
          message: "Error in calculation",
          points: pointsAssigned?.points,
          formula: pointsAssigned?.formula,
          userIsCreated,
        });
      }

      const newPoints = new PointsModel({
        userId,
        game,
        task,
        points,
        formula,
      });
      const newPointsSaved = await newPoints.save();

      // update user with new action
      const newAction = {
        timestamp: new Date(),
        points,
        formula,
      };
      const updatedUser = await UserModel.findByIdAndUpdate(
        user?._id,
        {
          $push: { actions: newAction },
        },
        { new: true }
      );

      res.status(201).json({
        message: "Points assigned successfully",
        points,
        formula,
        userIsCreated,
      });
    } catch (error) {
      console.error(error);
      res.status(500).send(error);
    }
  }
}

export { PointsController };
