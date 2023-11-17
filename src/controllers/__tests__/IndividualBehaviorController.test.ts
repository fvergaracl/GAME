import IndividualBehaviorController from "../IndividualBehaviorController";
import { TaskModel } from "../../models/TaskModel";
import { Request, Response } from "express";

jest.mock("../../models/TaskModel");

describe("IndividualBehaviorController", () => {
  it("correctly calculates the average time between tasks", async () => {
    // Mock the TaskModel.find method to return a fixed set of tasks

    TaskModel.find = jest.fn().mockImplementation(() => ({
      sort: jest
        .fn()
        .mockResolvedValue([
          { timestamp: new Date("2020-01-01T10:00:00Z") },
          { timestamp: new Date("2020-01-01T11:00:00Z") },
          { timestamp: new Date("2020-01-01T12:30:00Z") },
        ]),
    }));

    // Create mock objects for request and response
    const req = {
      params: { id_user: "1", game_id: "1" },
    } as unknown as Request;

    const res = {
      json: jest.fn(),
      status: jest.fn().mockReturnThis(),
      send: jest.fn(),
    } as unknown as Response;
    // Execute the controller method
    await IndividualBehaviorController.calculateIndividualGameBehavior(
      req,
      res
    );

    // Verify the result
    // toHaveBeenCalledTimes

    expect(res.json).toHaveBeenCalledTimes(1);
    expect(res.json).toHaveBeenCalledWith({
      averageTime: 4500000,
      tasksMeasured: 3,
    });
  });

  it("returns null for average time when there are no tasks", async () => {
    // Mock the TaskModel.find method to return an empty array
    TaskModel.find = jest.fn().mockImplementation(() => ({
      sort: jest.fn().mockResolvedValue([]),
    }));

    // Create mock objects for request and response
    const req = {
      params: { id_user: "1", game_id: "1" },
    } as unknown as Request;

    const res = {
      json: jest.fn(),
      status: jest.fn().mockReturnThis(),
      send: jest.fn(),
    } as unknown as Response;

    // Execute the controller method
    await IndividualBehaviorController.calculateIndividualGameBehavior(
      req,
      res
    );

    // Verify the result
    expect(res.json).toHaveBeenCalledTimes(1);
    expect(res.json).toHaveBeenCalledWith({
      averageTime: null,
      tasksMeasured: 0,
    });
  });

  it("returns null for average time when there is only one task", async () => {
    // Mock the TaskModel.find method to return a single task
    TaskModel.find = jest.fn().mockImplementation(() => ({
      sort: jest.fn().mockResolvedValue([{ timestamp: new Date() }]),
    }));

    // Create mock objects for request and response
    const req = {
      params: { id_user: "1", game_id: "1" },
    } as unknown as Request;

    const res = {
      json: jest.fn(),
      status: jest.fn().mockReturnThis(),
      send: jest.fn(),
    } as unknown as Response;

    // Execute the controller method

    await IndividualBehaviorController.calculateIndividualGameBehavior(
      req,
      res
    );
    // const jsonRes = (res.json as jest.Mock).mock.calls[0][0];
    // console.log(jsonRes);

    // Verify the result
    expect(res.json).toHaveBeenCalledTimes(1);
    expect(res.json).toHaveBeenCalledWith({
      averageTime: null,
      tasksMeasured: 1,
    });
  });

  it("returns an error when there is an unexpected error", async () => {
    // Mock the TaskModel.find method to throw an error
    TaskModel.find = jest.fn().mockImplementation(() => {
      throw new Error("Unexpected error");
    });

    // Create mock objects for request and response
    const req = {
      params: { id_user: "1", game_id: "1" },
    } as unknown as Request;

    const res = {
      json: jest.fn(),
      status: jest.fn().mockReturnThis(),
      send: jest.fn(),
    } as unknown as Response;

    // Execute the controller method
    await IndividualBehaviorController.calculateIndividualGameBehavior(
      req,
      res
    );

    // Verify the result
    expect(res.status).toHaveBeenCalledTimes(1);
    expect(res.status).toHaveBeenCalledWith(500);
    expect(res.send).toHaveBeenCalledTimes(1);
    expect(res.send).toHaveBeenCalledWith(
      "An error occurred while calculating the game behavior."
    );
  });
});
