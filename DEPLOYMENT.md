# Deploying GAME 🌍

> 📚 **Canonical reference:** the exhaustive operations guide - topology, the
> `Makefile` targets, scaling, health/graceful-shutdown, and runbooks - lives
> in the docs site at [`docs/source/operations.rst`](docs/source/operations.rst),
> and **every** configuration variable in
> [`docs/source/configuration.rst`](docs/source/configuration.rst). This page
> is the quick-start.

This guide provides step-by-step instructions for deploying the GAME project in both local development and production environments.

## Prerequisites

Ensure you have the following installed and configured before starting the deployment:

- **Docker**: For containerizing the application and the database.
- **Docker Compose**: To orchestrate multi-container Docker applications.
- **Kubernetes** (Optional for production): If deploying to a Kubernetes cluster, ensure you have access to a properly configured cluster and `kubectl` installed.


## Local Deployment with Docker 🐳

For local development the project ships **one-command launchers** that create your
`.env`, build the images, start the full stack, and wait until the API is healthy.

### Steps:

1. **Clone the repository**:

   ```bash
   git clone https://github.com/fvergaracl/GAME.git
   cd GAME
   ```

2. **Start the stack** with a single command:

   **Linux / macOS / WSL** (via the `Makefile`):

   ```bash
   make dev      # start the dev stack
   make logs     # follow logs
   make down     # stop
   ```

   **Windows** (PowerShell):

   ```powershell
   .\start.ps1           # start the dev stack
   .\start.ps1 -Logs     # start and follow logs
   .\start.ps1 -Down     # stop
   ```

   Both wrap `docker-compose-dev.yml`. Prefer to drive Compose yourself?

   ```bash
   docker-compose -f docker-compose-dev.yml up --build
   docker-compose -f docker-compose-dev.yml down --remove-orphans
   ```

3. **Access the application**:

   - API: <http://localhost:8000>
   - Swagger UI: <http://localhost:8000/docs>
   - ReDoc: <http://localhost:8000/redocs>
   - Dashboard: <http://localhost:3000>


## Production Deployment 🚀

For deploying the GAME application in a production environment, use the standard `docker-compose.yml` file. This setup assumes you have Docker installed on your server. (On Linux/macOS you can drive it through the `Makefile` as well: `make up FILE=docker-compose.yml` and `make down FILE=docker-compose.yml`. The Windows `start.ps1` launcher targets the **dev** stack only.)

### Steps:

1. **Set environment variables**:

   Ensure that your `.env` file contains production-level values, such as your database credentials, API keys, and other configuration settings. The `.env.sample` file can serve as a template.

2. **Build and deploy the services**:

   Run the following command to build and start the application and database in production mode:

   ```bash
   docker-compose up --build -d
   ```

   The `-d` flag will run the containers in detached mode (in the background).

3. **Check service status**:

   You can verify that the containers are running by checking the logs:

   ```bash
   docker-compose logs -f
   ```

4. **Scaling the application**:

   If you need to scale the application to handle more traffic, you can increase the number of application instances by running:

   ```bash
   docker-compose up --scale app=3
   ```

   This will start 3 instances of the `app` service, ensuring better load distribution.

5. **Stop the services**:

   To stop the containers in a production environment, use:

   ```bash
   docker-compose down
   ```


## Deploying to Kubernetes ☸️

If you're deploying GAME on a Kubernetes cluster, follow the steps in the [KUBERNETES_SETUP.md](KUBERNETES_SETUP.md) file for detailed instructions on setting up your cluster and deploying the application.


## Database Migrations

After deploying the application, you may need to apply database migrations to ensure the database schema is up to date.

1. **Apply migrations**:

   To apply all pending migrations, run the following command inside the running container:

   ```bash
   docker-compose exec app alembic upgrade head
   ```

   This will ensure the database schema matches the current state of the application.

## Health Checks

It’s a good practice to monitor the health of the application. You can set up health checks in Docker or Kubernetes to automatically restart any failed containers.

1. **Docker Health Check**:

   To configure a Docker health check, you can add a health check instruction in your Dockerfile or Docker Compose file.

2. **Kubernetes Health Check**:

   When using Kubernetes, you can define `liveness` and `readiness` probes in your deployment manifest to monitor the health of your pods.


## Rolling Back

In case something goes wrong during deployment, Docker and Kubernetes allow for easy rollback mechanisms.

1. **Docker Rollback**:

   If using Docker, simply stop the current containers and redeploy a previous version of the application by specifying an earlier image tag.

2. **Kubernetes Rollback**:

   Kubernetes keeps track of all deployments, allowing you to rollback to a previous version using:

   ```bash
   kubectl rollout undo deployment/<your-deployment-name>
   ```

By following these steps, you should be able to successfully deploy GAME in local and production environments using Docker and optionally Kubernetes. For more advanced deployment configurations, such as multi-node Kubernetes clusters, please consult the relevant cloud provider’s documentation or the Kubernetes community resources.
