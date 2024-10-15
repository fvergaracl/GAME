
# Running Tests for GAME 🧪

Testing is a critical part of the GAME project to ensure code quality, maintainability, and stability. This guide explains how to run tests, check code coverage, and write new tests for the project.

## Running Tests

The GAME project uses `pytest` for running both unit and integration tests. All test files are located in the `tests/` directory and follow the structure of the application.

### Steps to Run Tests

1. **Activate the Poetry environment**:

   Before running tests, ensure you are working in the Poetry environment:

   ```bash
   poetry shell
   ```

2. **Run all tests**:

   To execute all the tests in the project, use:

   ```bash
   poetry run pytest
   ```

   This will discover and run all the tests defined in the `tests/` directory.

3. **Run a specific test file**:

   If you want to run tests from a specific file, provide the path to the test file:

   ```bash
   poetry run pytest tests/test_your_file.py
   ```

4. **Run tests in verbose mode**:

   For more detailed output about the tests being run, add the `-v` flag:

   ```bash
   poetry run pytest -v
   ```


## Checking Code Coverage 📊

To ensure that your tests cover as much code as possible, you can generate a coverage report using the `pytest-cov` plugin. This is helpful for identifying parts of the codebase that are not tested.

### Steps to Run Tests with Coverage

1. **Run tests with coverage report in the terminal**:

   To check code coverage and get a report directly in the terminal, run:

   ```bash
   poetry run pytest --cov=app --cov-report=term-missing
   ```

   This command will show which parts of the code were covered by the tests and highlight any missing coverage.

2. **Generate an HTML coverage report**:

   For a more detailed, interactive view of the coverage, generate an HTML report:

   ```bash
   poetry run pytest --cov=app --cov-report=html
   ```

   After running this command, open the generated `htmlcov/index.html` file in your browser to view the report.


## Writing New Tests 📝

When contributing to the GAME project, ensure that you write appropriate tests for any new features or bug fixes. Here are some best practices:

1. **Test Structure**:
   - Place your tests in the `tests/` directory.
   - Name your test files with the prefix `test_` (e.g., `test_feature.py`).
   - Ensure your test functions follow the `test_` naming convention (e.g., `def test_new_feature()`).

2. **Unit Tests**:
   - Unit tests should test individual functions or methods in isolation.
   - Use mocking for dependencies like external APIs or databases to keep the tests fast and isolated.

3. **Integration Tests**:
   - Integration tests verify that different components of the system work together as expected.
   - These tests might involve actual database queries or interaction with external systems.

4. **Running Specific Tests**:
   - To run specific tests during development, you can use the `-k` flag followed by part of the test name:

     ```bash
     poetry run pytest -k "test_new_feature"
     ```

5. **Using Fixtures**:
   - `pytest` provides a powerful fixture system to manage common setup and teardown code.
   - Define reusable fixtures in the `conftest.py` file to simplify your tests and avoid redundancy.


## Running Tests in CI/CD

When submitting changes, all tests are automatically run in the Continuous Integration/Continuous Deployment (CI/CD) pipeline to ensure that the code is stable before merging.

If you want to replicate the CI/CD environment locally:

1. **Run the test suite with code coverage**:

   ```bash
   poetry run pytest --cov=app
   ```

2. **Verify that all tests pass and the coverage threshold is met**.


## Test Coverage Goals

The GAME project aims to maintain high code coverage across all modules. While not all code needs 100% coverage, contributors should strive to ensure that new features and critical paths are thoroughly tested. Maintaining comprehensive test coverage ensures stability and minimizes the risk of bugs in production.

To check the current coverage status, visit the [Codecov page](https://codecov.io/gh/fvergaracl/GAME) or review the coverage badge on the project’s main repository page.


## Common Commands Cheat Sheet

| Command                                     | Description                                      |
| ------------------------------------------- | ------------------------------------------------ |
| `poetry run pytest`                         | Run all tests                                    |
| `poetry run pytest -v`                      | Run all tests in verbose mode                    |
| `poetry run pytest --cov=app`               | Run all tests with coverage reporting            |
| `poetry run pytest --cov=app --cov-report=html` | Generate an HTML report for test coverage     |
| `poetry run pytest -k "test_specific_case"` | Run only the tests matching the specific case    |
| `poetry run pytest tests/test_file.py`      | Run tests in a specific file                     |
| `poetry run pytest --cov=app --cov-report=term-missing` | Run tests with coverage and display any missing lines in the terminal |
---


By following this guide, you'll be able to run, write, and enhance tests for the GAME project. Thorough testing is essential for the project's stability and growth, so please ensure all code changes are accompanied by appropriate test coverage. If you encounter any issues or have questions about writing tests, feel free to open an issue in the repository.
