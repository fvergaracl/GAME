import express from "express";
import { app } from "./app";
import { initDefaultApiKeys } from "./services";

const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
  initDefaultApiKeys();
  console.log(`Server is running on port ${PORT}`);
});
