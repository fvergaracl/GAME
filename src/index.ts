import { app } from "./app";
import { initDefaultApiKeys } from "./services";
import { connectDB } from "./database";

const PORT = process.env.PORT || 3000;

connectDB()
  .then(() => {
    initDefaultApiKeys();
    app.listen(PORT, () => {
      console.log(`Servidor escuchando en el puerto ${PORT}`);
    });
  })
  .catch((error) => {
    console.error("Error al conectar a la base de datos:", error);
    process.exit(1);
  });
