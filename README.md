# GAME (Goals And Motivation Engine) 🎮

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
