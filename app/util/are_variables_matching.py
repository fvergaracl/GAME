
def are_variables_matching(new_variables, old_variables):
    """
    Compare two dictionaries to see if they match an value in the schema

    :param new_variables: The new variables to compare
    :param old_variables: The old variables to compare against

    :return: True if the game matches the schema, False otherwise
    """
    for key, value in new_variables.items():
        if key in old_variables:
            if old_variables[key] != value:
                return False
    return True
