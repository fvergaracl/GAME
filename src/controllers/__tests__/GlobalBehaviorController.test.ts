import calculateGlobalGameBehavior from "../GlobalBehaviorController";
import { TaskModel } from "../../models/TaskModel";
import { Request, Response } from "express";
import GlobalBehaviorController from "../GlobalBehaviorController";

jest.mock("../../models/TaskModel");

describe("IndividualBehaviorController", () => {
  it("should correctly calculate global game behavior for multiple users", async () => {
    // Mock the TaskModel.find method to return a fixed set of tasks
    TaskModel.find = jest.fn().mockImplementation(() => ({
      sort: jest.fn().mockResolvedValue([
        { idUser: "1", timestamp: new Date("2020-01-01T10:00:00Z") },
        { idUser: "1", timestamp: new Date("2020-01-01T11:00:00Z") },
        { idUser: "2", timestamp: new Date("2020-01-01T12:30:00Z") },
        { idUser: "2", timestamp: new Date("2020-01-01T13:30:00Z") },
        { idUser: "2", timestamp: new Date("2020-01-01T14:30:00Z") },
      ]),
    }));

    // Create mock objects for request and response
    const req = {
      params: { game_id: "1" },
    } as unknown as Request;

    const res = {
      json: jest.fn(),
      status: jest.fn().mockReturnThis(),
      send: jest.fn(),
    } as unknown as Response;

    // Execute the controller method
    await GlobalBehaviorController.calculateGlobalGameBehavior(req, res);

    // Verify the result
    expect(res.json).toHaveBeenCalledTimes(1);
    expect(res.json).toHaveBeenCalledWith({
      globalAverageTime: 3600000,
      tasksMeasured: 5,
    });
  });

  it("should return null for global average time when there are no tasks", async () => {
    // Mock the TaskModel.find method to return an empty array
    TaskModel.find = jest.fn().mockImplementation(() => ({
      sort: jest.fn().mockResolvedValue([]),
    }));

    // Create mock objects for request and response
    const req = {
      params: { game_id: "1" },
    } as unknown as Request;

    const res = {
      json: jest.fn(),
      status: jest.fn().mockReturnThis(),
      send: jest.fn(),
    } as unknown as Response;

    // Execute the controller method
    await GlobalBehaviorController.calculateGlobalGameBehavior(req, res);

    // Verify the result
    expect(res.json).toHaveBeenCalledTimes(1);
    expect(res.json).toHaveBeenCalledWith({
      globalAverageTime: null,
      tasksMeasured: 0,
    });
  });
  it("should return null for global average time when each user has only one task", async () => {
    // Mock the TaskModel.find method to return a fixed set of tasks

    TaskModel.find = jest.fn().mockImplementation(() => ({
      sort: jest.fn().mockResolvedValue([
        { idUser: "1", timestamp: new Date("2020-01-01T10:00:00Z") },
        { idUser: "2", timestamp: new Date("2020-01-01T11:00:00Z") },
      ]),
    }));

    // Create mock objects for request and response
    const req = {
      params: { game_id: "1" },
    } as unknown as Request;

    const res = {
      json: jest.fn(),
      status: jest.fn().mockReturnThis(),
      send: jest.fn(),
    } as unknown as Response;

    // Execute the controller method
    await GlobalBehaviorController.calculateGlobalGameBehavior(req, res);

    // Verify the result
    expect(res.json).toHaveBeenCalledTimes(1);
    expect(res.json).toHaveBeenCalledWith({
      globalAverageTime: null,
      tasksMeasured: 2,
    });
  });
});
