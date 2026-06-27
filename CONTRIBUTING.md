# Contributing to GAME 💪

We welcome contributions from developers of all levels! Whether you're fixing a bug, adding a feature, or improving documentation, your contributions are valuable to us.

## How to Contribute

1. **Fork** the repository by clicking the "Fork" button at the top of the repository page.
2. **Clone** your forked repository to your local machine:

   ```bash
   git clone https://github.com/<your-username>/GAME.git
   ```

3. **Create a new branch** for your feature or bug fix:

   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **Make your changes**. Ensure that your code is clean, follows project conventions, and is properly documented.
5. **Test your changes** to make sure everything works as expected. You can run the test suite using:

   ```bash
   poetry run pytest
   ```

6. **Commit your changes** with a meaningful commit message:

   ```bash
   git commit -m "Add feature/fix bug: detailed description"
   ```

7. **Push your changes** to your forked repository:

   ```bash
   git push origin feature/your-feature-name
   ```

8. **Submit a pull request** (PR) from your forked repository to the main GAME repository. Include a clear description of your changes in the PR.


> [!NOTE]
> Be sure to provide detailed information about the feature or bug fix in your pull request, and reference any related issues if applicable.

## Development Workflow

### Setting Up the Project

1. **Clone the repository**:

   ```bash
   git clone https://github.com/fvergaracl/GAME.git
   cd GAME
   ```

2. **Install dependencies** using Poetry:

   ```bash
   poetry install
   ```

3. **Activate the Poetry environment**:

   ```bash
   poetry shell
   ```

4. **Start the development server**:

   ```bash
   poetry run uvicorn app.main:app --reload
   ```

   This will start the API server locally, and any changes you make will automatically reload the application.


## Writing Tests 🧪

All contributions should include relevant unit and/or integration tests to ensure the stability of the codebase. You can find existing tests in the `tests/` directory.

To run the tests:

```bash
poetry run pytest
```

To run tests with code coverage:

```bash
poetry run pytest --cov=app --cov-report=term-missing
```



## Code Style Guidelines 📝

We follow PEP 8 for Python code. Formatting and linting are enforced in CI with
[`black`](https://black.readthedocs.io/), [`isort`](https://pycqa.github.io/isort/)
(configured with the `black` profile so the two never disagree) and
[`ruff`](https://docs.astral.sh/ruff/). Before submitting your pull request, run:

```bash
poetry run black .                # auto-format
poetry run isort .                # auto-sort imports
poetry run ruff check . --fix     # lint (and auto-fix what it safely can)
```

To check without modifying files (this is exactly what CI runs):

```bash
poetry run ruff check .
poetry run black --check .
poetry run isort --check-only .
```

### Pre-commit hooks (recommended)

Install the local hooks once so the lint gate runs automatically on every commit
and you catch issues before they reach CI:

```bash
poetry run pre-commit install          # wire up the git hook (one time)
poetry run pre-commit run --all-files  # run against the whole repo on demand
```

The hooks in [`.pre-commit-config.yaml`](.pre-commit-config.yaml) mirror the CI
lint gate exactly — `ruff`, `black` and `isort` in `--check` mode, pinned to the
same versions as the backend. A failing hook means CI would fail too; fix it with
the auto-format commands above and re-commit.

## Required CI checks ✅

The following checks run on every push and pull request and **must pass** before a
PR can be merged:

| Check | Workflow | What it enforces |
| --- | --- | --- |
| **Lint** | `.github/workflows/lint.yml` | `ruff check .`, `black --check .` and `isort --check-only .` all pass. Any failure turns the PR red — formatting and lint are no longer auto-fixed for you. |
| **Test & Coverage** | `.github/workflows/coverage.yml` | `pytest` passes and total `app/` coverage stays **≥ 93%** (`--cov-fail-under=93`). Deleting tests or adding uncovered code that drops below the floor fails the PR. |
| **pytest (unit)** | `.github/workflows/pytest.yml` | The unit test suite passes. |
| **Dashboard CI** | `.github/workflows/dashboard-ci.yml` | Frontend only (`dashboard/**`): `npm ci` + ESLint + Vitest with a coverage floor. |

> [!NOTE]
> CI no longer pushes "Automated Black & Isort" commits to your branch. You are
> responsible for formatting locally (`black .` + `isort .`) before pushing; the
> lint check only verifies, it does not modify your code.


## Reporting Issues 🐛

If you encounter any bugs or have feature requests, please open an issue in the [GitHub Issues](https://github.com/fvergaracl/GAME/issues) section. Make sure to provide as much detail as possible, including:

- A clear description of the problem or feature request.
- Steps to reproduce the issue (if applicable).
- The expected outcome.
- Any relevant logs or error messages.

We encourage community discussions on issues, so feel free to comment if you can help resolve a problem!


## Join the Community 💬

If you have any questions, suggestions, or want to discuss potential features, you can reach out to us by creating an issue or starting a discussion on the [GitHub Discussions](https://github.com/fvergaracl/GAME/discussions) page.

Thank you for contributing to GAME!
