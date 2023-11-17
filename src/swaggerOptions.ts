const options = {
  definition: {
    openapi: "3.0.0", // Specification (optional, defaults to swagger: '2.0')
    info: {
      title: "Gamification Engine", // Title (required)
      version: "0.1.0", // Version (required)
    },
  },
  apis: ["./routes/*.ts"], // Path to the API docs
};

export { options };
