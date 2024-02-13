# GAME (Goals And Motivation Engine) 🎮

Coverage: [0-9]\*%

## Description 📝

GAME (Goals And Motivation Engine) is a system designed to foster motivation and achievement of goals through gamification. This open-source project utilizes a PostgreSQL database and is developed with FastAPI in Python, managed via Poetry for environment handling.

## Requirements 🛠️

- Python 3.8+
- PostgreSQL
- Docker and Docker Compose (optional, for local database deployment)
- Poetry

## Project Structure 📂

The GAME project is structured to facilitate easy navigation and understanding for developers looking to contribute or integrate new features. Below is an overview of the project's directory structure and a brief explanation of each component:

```
.
├── alembic.ini                   # Configuration for Alembic migrations
├── app                           # Main application directory
│   ├── api                       # API route definitions
│   │   └── v1                    # Version 1 of the API
│   │       ├── endpoints         # API endpoints
│   │       └── routes.py         # API route registrations
│   ├── core                      # Core application components (config, security)
│   ├── model                     # Database models
│   ├── repository                # Data access layer
│   ├── schema                    # Pydantic schemas for request and response objects
│   ├── services                  # Business logic layer
│   └── util                      # Utility functions and classes
├── classes.png                   # Class diagram (if applicable)
├── default_strategy.json         # Default strategy configuration
├── deployFiles                   # Deployment related files (if applicable)
├── doc                           # Documentation files and images
├── docker                        # Dockerfiles for containerization
├── docker-compose-dev.yml        # Docker Compose for development
├── docker-compose.yml            # Docker Compose for production
├── migrations                    # Alembic migrations
├── packages.png                  # Package diagram (if applicable)
├── poetry.lock                   # Poetry lock file (dependencies)
├── pyproject.toml                # Poetry configuration and project metadata
├── README.md                     # Project README
├── requirements.txt              # Python requirements (for non-Poetry environments)
├── strategies.md                 # Documentation on strategy patterns used
└── tests                         # Test suite (unit and integration tests)
```

### Details

This table uses emojis to denote the type of content (📁 for directories, 📄 for files) and provides a brief description to help in understanding their purpose:

| Type | Path                         | Description                                                                                        |
| ---- | ---------------------------- | -------------------------------------------------------------------------------------------------- |
| 📁   | `/app`                       | Root directory for application code. Contains all the service logic, models, and API endpoints.    |
| 📁   | `/app/api/v1`                | Contains version 1 of the API endpoints. This is where you define all the route handlers.          |
| 📄   | `/app/api/v1/endpoints/*.py` | API endpoint files like `games.py`, `strategy.py`, etc., defining the logic for each endpoint.     |
| 📁   | `/app/core`                  | Core configurations and utilities for the app, including database connection and configurations.   |
| 📁   | `/app/model`                 | Definitions of database models, mapping the database schema to Python code.                        |
| 📁   | `/app/repository`            | Data access layer, containing files that interact with the database models.                        |
| 📁   | `/app/schema`                | Schemas for request and response validation and serialization.                                     |
| 📁   | `/app/services`              | Business logic layer, where the main application operations are defined.                           |
| 📄   | `/app/main.py`               | The entry point for the Flask application. Contains app initialization and route definitions.      |
| 📄   | `/docker-compose.yml`        | Docker Compose configuration file for local development, defining how your containers are built.   |
| 📁   | `/docker`                    | Contains Dockerfiles for different services, useful for containerizing your application.           |
| 📁   | `/kubernetes`                | Kubernetes configurations for deployment, including deployments, services, and persistent volumes. |
| 📁   | `/migrations`                | Alembic migrations for database schema management. Contains scripts for database versioning.       |
| 📁   | `/tests`                     | Contains all the test code, including unit and integration tests, organized by test type.          |
| 📄   | `/README.md`                 | The main documentation file for the project, explaining how to set up and run the project.         |

## Environment Setup 🌐

### Environment Variables

Before starting the project, it's necessary to configure the environment variables. Copy the environment variables defined in `.env.sample` to `.env`. Below is an example and explanation of each variable:

```
VERSION_APP="1.0.0" # Version of GAME API
ENV=dev # Indicates whether the environment is development or production (dev|production)
DB_ENGINE=postgresql # Database engine
DB_NAME=game_dev_db # Database name
DB_USER=root # Database user
DB_PASSWORD=example # Database password
DB_HOST=localhost # Database host
DB_PORT=5432 # Database port
DEFAULT_CONVERSION_RATE_POINTS_TO_COIN=100 # Default conversion rate of points to coins
DATABASE_URL=postgresql://root:example@localhost:5432/game_dev_db # Database connection URL
```

### Activating the Poetry Environment

To activate the Poetry environment, run:

```
poetry shell
```

If it's your first time running the project, install all dependencies with:

```
poetry install
```

### Database Deployment with Docker Compose

To bring up the database locally, run:

```
docker-compose -f docker-compose.yml up --build
```

If it's the first time deploying the database, you should initialize it with Alembic:

```
alembic upgrade head
```

### Deploying the REST API

To deploy the REST API, run:

```
uvicorn app.main:app --reload
```

## Docker 🐳

### Overview

Docker provides a way to run applications securely isolated in a container, packaged with all its dependencies and libraries. For the GAME project, Docker and Docker Compose are used to simplify the deployment of the PostgreSQL database and the FastAPI application, ensuring consistent environments from development to production.

### Requirements

- Docker
- Docker Compose

### Setting up Docker

Ensure Docker and Docker Compose are installed on your machine. Docker Compose will use the `docker-compose.yml` for production deployments and `docker-compose-dev.yml` for development environments.

### Configuration Files

- `Dockerfile`: Contains the instructions for building the application's Docker image.
- `docker-compose.yml`: Defines the production services, networks, and volumes.
- `docker-compose-dev.yml`: Used for setting up the development environment with Docker Compose.

### Using Docker Compose

#### Development Environment

To set up the development environment, run:

```bash
docker-compose -f docker-compose-dev.yml up --build
```

This command builds the application image from the Dockerfile, sets up the PostgreSQL database, and runs the application in development mode.

#### Production Environment

For production deployment, use:

```bash
docker-compose up --build
```

This will pull the necessary images, set up the database, and run the application in production mode.

### Building and Running Docker Containers

- To build the Docker image for the application, navigate to the directory containing the Dockerfile and run:

  ```bash
  docker build -t gamification-engine .
  ```

- To run the application using Docker directly, you can use:

  ```bash
  docker run -p 80:80 gamification-engine
  ```

## Kubernetes ☸️

### Prerequisites

- Kubernetes cluster: You can set up a cluster on cloud platforms like Google Kubernetes Engine (GKE), Amazon Elastic Kubernetes Service (EKS), Azure Kubernetes Service (AKS), or on-premises using Minikube or kubeadm.
- kubectl: The Kubernetes command-line tool, `kubectl`, allows you to run commands against Kubernetes clusters.

### Configuration Files Overview

You've uploaded several configuration files, which are crucial for deploying applications on Kubernetes. Here's a brief overview of each:

1. **`deploy-kubernetes.sh`**: Likely a shell script to automate the deployment process.
2. **`env-prod-configmap.yaml`**: Defines environment variables for your applications in a ConfigMap, making it easier to configure different environments.
3. **`postgres-data-persistentvolumeclaim.yaml`**: Creates a PersistentVolumeClaim (PVC) for PostgreSQL, ensuring data persists across pod restarts.
4. **`ingress.yaml`**: Defines rules for routing external HTTP(S) traffic to your services.
5. **`gamificationengine-service.yaml`**: Configures a service for the gamification engine, making it accessible within the cluster.
6. **`postgres-service.yaml`**: Creates a service for PostgreSQL, allowing other components to communicate with the database.
7. **`postgres-deployment.yaml`**: Defines the deployment for a PostgreSQL database, including its container image, environment variables, and storage.
8. **`gamificationengine-deployment.yaml`**: Describes the deployment for your gamification engine application.
9. **`.env`**: Contains environment variables for your setup, not directly used by Kubernetes but could be used by your scripts or applications.

### Steps to Deploy

The `deploy-kubernetes.sh` script is designed to automate the deployment of Kubernetes resources with the following options:

- **`--postgres`**: Apply only the PostgreSQL deployment and its dependencies. This option is useful for setting up or updating the database component of your application without affecting other parts.

- **`--api`**: Apply only the API deployment and its dependencies. This allows for deploying or updating the API layer separately, which can be particularly handy for rolling updates or when testing new API features.

- **`--verbose`**: Display verbose output. When this flag is used, the script provides more detailed information about the commands being executed, which is helpful for debugging or for more detailed logging purposes.

- **`--help`**: Display the help message. This option shows usage information, including a description of each flag and examples of how to use the script.

```bash
bash deploy-kubernetes.sh
```

### Steps to Deploy (Manually)

#### 1. Set up your Kubernetes cluster

Ensure your Kubernetes cluster is up and running.

#### 2. Configure kubectl

Configure `kubectl` to connect to your Kubernetes cluster. This step varies depending on your cloud provider or local setup.

#### 3. Apply Configuration Files

Navigate to the directory containing your Kubernetes configuration files and apply them using `kubectl`. For example:

```bash
kubectl apply -f env-prod-configmap.yaml
kubectl apply -f postgres-data-persistentvolumeclaim.yaml
kubectl apply -f ingress.yaml
kubectl apply -f gamificationengine-service.yaml
kubectl apply -f postgres-service.yaml
kubectl apply -f postgres-deployment.yaml
kubectl apply -f gamificationengine-deployment.yaml
```

#### 4. Monitor Deployment Status

You can monitor the status of your deployments using:

```bash
kubectl get pods
kubectl get services
kubectl describe deployment <deployment-name>
```

#### 5. Access Your Application

- **Ingress**: If you're using an ingress, you'll need to configure DNS for your domain to point to your ingress IP.
- **Port-Forwarding**: For quick access or testing, you can use `kubectl port-forward`.

```bash
kubectl port-forward service/gamificationengine-service 8080:80
```

## Other Useful Commands 🚀

### Alembic (Database Migrations)

- `alembic upgrade head`: Applies all migrations.
- `alembic downgrade base`: Reverts all migrations.
- `alembic revision --autogenerate -m "revision_name"`: Creates a new migration.
- `alembic history`: Shows Alembic revision history.

### Server

- `uvicorn app.main:app --reload`: Runs the development server.
  - Options:
    - `--host 0.0.0.0`: Specifies the host.
    - `--port 8000`: Specifies the port.

### Testing

- `pytest`: Runs basic tests.
- `pytest --cov=app --cov-report=term-missing`: Runs tests with coverage and displays the report in the terminal.
- `pytest --cov=app --cov-report=html`: Generates a coverage report in HTML.
