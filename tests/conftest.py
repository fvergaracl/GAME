import pytest
from prettytable import PrettyTable

# Custom pytest hook to capture variables on test failure


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # Execute all other hooks to obtain the report object
    outcome = yield
    rep = outcome.get_result()

    # Check if the test has failed
    if rep.when == "call" and rep.failed:
        # Access the request object to get the test function's local variables
        test_function = item.function
        frame = test_function.__code__.co_varnames

        # Get the variables from the function's frame
        local_variables = {
            var: item.funcargs[var] for var in frame if var in item.funcargs
        }

        # Show variables in a pretty table format
        if local_variables:
            table = PrettyTable()
            table.field_names = ["Variable Name", "Value"]
            for var_name, value in local_variables.items():
                table.add_row([var_name, value])
