const { version, title, description } = require("../package.json");

const swaggerDefinition = {
  openapi: "3.0.0",
  info: {
    title,
    description,
    version,
  },
  servers: [
    {
      url: "http://localhost:3000",
      description: "Development server",
    },
  ],
};

const options = {
  swaggerDefinition,
  apis: ["./src/routes/*.ts"],
};

export { options };
