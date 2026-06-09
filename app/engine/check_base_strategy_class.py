import logging

logger = logging.getLogger(__name__)


def check_class_methods_and_variables(Class_to_check, debug=False):
    """Check that a class exposes every method and variable a strategy needs.

    Args:
        Class_to_check: The strategy class to validate.
        debug (bool): When ``True``, log which member is missing.

    Returns:
        bool: ``True`` if the class has all the expected methods and
        variables, ``False`` otherwise.
    """
    instance = Class_to_check()

    methods = [
        "get_strategy_id",
        "get_strategy_name",
        "get_strategy_description",
        "get_strategy_name_slug",
        "get_strategy_version",
        "get_variable_basic_points",
        "get_variable_bonus_points",
        "set_variables",
        "get_variables",
        "get_variable",
        "set_variable",
        "get_strategy",
        "calculate_points",
        "generate_logic_graph",
    ]

    variables = [
        "strategy_name",
        "strategy_description",
        "strategy_name_slug",
        "strategy_version",
    ]

    missing_methods = [method for method in methods if not hasattr(instance, method)]
    if missing_methods:
        logger.warning("Missing methods: %s", missing_methods)
    else:
        logger.info("All methods are present.")

    missing_variables = [
        variable for variable in variables if not hasattr(instance, variable)
    ]
    if debug:
        if missing_variables:
            logger.warning("Missing variables: %s", missing_variables)
        else:
            logger.info("All variables are present.")

    return not missing_methods and not missing_variables
