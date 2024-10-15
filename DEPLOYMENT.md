# Deploying GAME 🌍

This guide provides step-by-step instructions for deploying the GAME project in both local development and production environments.

## Prerequisites

Ensure you have the following installed and configured before starting the deployment:

- **Docker**: For containerizing the application and the database.
- **Docker Compose**: To orchestrate multi-container Docker applications.
- **Kubernetes** (Optional for production): If deploying to a Kubernetes cluster, ensure you have access to a properly configured cluster and `kubectl` installed.


## Local Deployment with Docker 🐳

For local development, Docker Compose simplifies the process of setting up the PostgreSQL database and the FastAPI server in one go.

### Steps:

1. **Clone the repository**:

   ```bash
   git clone https://github.com/fvergaracl/GAME.git
   cd GAME
   ```

2. **Start the services with Docker Compose**:

   To spin up both the PostgreSQL database and the FastAPI server, run:

   ```bash
   docker-compose -f docker-compose-dev.yml up --build
   ```

   This will build the Docker images and start the containers in a local development environment.

3. **Access the application**:

   Once the containers are running, you can access the API at:

   ```bash
   http://localhost:8000
   ```

   - For the automatic API documentation (Swagger UI), go to:
     ```bash
     http://localhost:8000/docs
     ```

   - For ReDoc documentation:
     ```bash
     http://localhost:8000/redoc
     ```

4. **Stop the services**:

   To stop the containers, use:

   ```bash
   docker-compose down
   ```


## Production Deployment 🚀

For deploying the GAME application in a production environment, use the standard `docker-compose.yml` file. This setup assumes you have Docker installed on your server.

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
