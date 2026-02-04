# GAME (Goals And Motivation Engine) 🎮

<p align="center">
  <img src="https://codecov.io/gh/fvergaracl/GAME/branch/main/graph/badge.svg?token=R0MGAOMUBU" alt="codecov">
  <img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="License Apache 2.0">
  <img src="https://img.shields.io/github/stars/fvergaracl/GAME" alt="GitHub Repo stars">
  <img src="https://img.shields.io/github/v/tag/fvergaracl/game?color=green" alt="Last TAG">

</p>

<p align="center">
  <img src="GAME_logo.png" alt="GAME Logo">
</p>

## Welcome to GAME! 🏆

**GAME** (Goals And Motivation Engine) is an open-source system designed to help individuals and organizations achieve their goals through gamification. This project aims to enhance motivation and engagement by introducing game-like mechanics in non-game contexts.

Built with **FastAPI** (Python) and utilizing **PostgreSQL** as the database, the project is managed with **Poetry** for dependency management. Docker and Kubernetes configurations are provided to simplify deployment and scaling.

## Key Features ✨

- 🚀 **FastAPI-based**: High-performance API with Python’s FastAPI framework.
- 🛠️ **Modular Design**: Clean architecture, easily extendable.
- 🐋 **Docker Support**: Ready-to-use Docker and Docker Compose setups.
- ☸️ **Kubernetes Ready**: Configuration provided for Kubernetes deployment.
- ✅ **Comprehensive Testing**: Fully integrated testing suite with `pytest` and Codecov for coverage tracking.

## Quick Start ⚡

To get started quickly, follow these steps to set up the project locally.

### 1. Clone the repository

```bash
git clone https://github.com/fvergaracl/GAME.git
cd GAME
```

### 2. Install dependencies with Poetry

Make sure you have Poetry installed, then run:

```bash
poetry env use python3
poetry install
```

### 3. Setup environment variables

Copy the sample environment variables file and configure it as needed:

```bash
cp .env.sample .env
```

### 4. Run the application

Start the FastAPI development server:

```bash
poetry run uvicorn app.main:app --reload
```

You can access the application at `http://localhost:8000`.

### 5. Access the API documentation

Swagger UI is available at `http://localhost:8000/docs` for easy API interaction and testing.

## Project Structure 📂

The GAME project follows a clean and modular structure to ensure maintainability and scalability. Below is an overview of the main components:

```
.
├── app                             # Main application directory
│   ├── api                         # API route definitions
│   ├── core                        # Core configurations and utilities
│   ├── models                      # Database models
│   ├── schemas                     # Pydantic schemas for validation
│   ├── services                    # Business logic and service layer
│   └── tests                       # Unit and integration tests
├── docker                          # Docker-related files
├── k8s                             # Kubernetes configuration files
├── migrations                      # Alembic migrations
├── pyproject.toml                  # Poetry configuration file
└── README.md                       # Project documentation
```

For a more detailed explanation of the project structure, check out the [SETUP.md](SETUP.md) file.

## Want to Contribute? 💡

We welcome contributions of all kinds! Whether you want to fix a bug, improve the documentation, or add a new feature, we encourage you to join the project.

Check out the [CONTRIBUTING.md](CONTRIBUTING.md) guide for more details on how to contribute.

## Running Tests 🧪

The project includes a suite of unit and integration tests to ensure code quality. To run the tests, use:

```bash
poetry run pytest
```

For coverage reporting, use:

```bash
poetry run pytest --cov=app --cov-report=term-missing
```

You can find more detailed information on testing in the [TESTING.md](TESTING.md) file.

## Deployment 🚀

### Docker

For local development and production environments, you can use Docker. To bring up the application with Docker Compose, run:

```bash
docker-compose up --build
```

For more details, refer to the [DOCKER_SETUP.md](DOCKER_SETUP.md) file.

### Kubernetes

The project is ready to be deployed to Kubernetes. You can find the configuration files in the `kubernetes/` directory. Follow the steps in the [KUBERNETES_SETUP.md](KUBERNETES_SETUP.md) for detailed instructions.

## License 📜

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

For any questions or feedback, feel free to open an issue or start a discussion in the [GitHub Issues](https://github.com/fvergaracl/GAME/issues) section. You can also check out our official documentation: [GAME Docs](https://fvergaracl.github.io/GAME).

---
