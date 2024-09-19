def check_class_methods_and_variables(Class_to_check, debug=False):
    """
    Check if the class has all the methods and variables expected for a
      base strategy.

    Args:
    Class_to_check: class
        The class to check.

    Returns:
    bool: True if the class has all the expected methods and variables,
      False otherwise.

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
        "generate_logic_graph"
    ]

    variables = [
        "strategy_name",
        "strategy_description",
        "strategy_name_slug",
        "strategy_version",
        "variable_basic_points",
        "variable_bonus_points",
    ]

    missing_methods = [method for method in methods if not hasattr(
        instance, method)]
    if missing_methods:
        print(f"Missing methods: {missing_methods}")
    else:
        print("[+] All methods are present.")

    missing_variables = [
        variable for variable in variables if not hasattr(instance, variable)
    ]
    if debug:
        if missing_variables:
            print(f"Missing variables: {missing_variables}")
        else:
            print("[+] All variables are present.")

    return not missing_methods and not missing_variables
