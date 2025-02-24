# Setting up GAME 🎮

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
│   ├── api                       # API route definitions
│   │   └── v1                    # Version 1 of the API
│   │       ├── endpoints         # API endpoints
│   │       └── routes.py         # API route registrations
│   ├── core                      # Core application components (config, security)
│   ├── model                     # Database models
│   ├── repository                # Data access layer
│   ├── schema                    # Pydantic schemas for request and response objects
│   ├── services                  # Business logic layer
│   └── util                      # Utility functions and classes
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
SECRET_KEY=secret
```

## Step-by-step Setup 🛠️

### 1. Clone the repository

```bash
git clone https://github.com/fvergaracl/GAME.git
cd GAME
```


### 2. Install dependencies

Activate Poetry and install the required packages:

```bash
poetry install
```

### 3. Setup environment variables

Copy `.env.sample` to `.env` and configure your database credentials:

```bash
cp .env.sample .env
```

### 4. Run database migrations

```bash
alembic upgrade head
```

### 5. Start the development server

```bash
poetry run uvicorn app.main:app --reload
```

For further details, check the [DEPLOYMENT.md](DEPLOYMENT.md).
