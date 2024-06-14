def are_variables_matching(new_variables, old_variables) -> bool:
    """
    Compares two dictionaries to determine if all key-value pairs in the first
      dictionary match those in the second dictionary. This comparison is used
      to verify if an updated set of variables ('new_variables') matches with
      a baseline ('old_variables') for consistency or change detection purposes
      . Only keys present in 'new_variables' are checked against
      'old_variables'; keys exclusive to 'old_variables' are not considered in
       the comparison.

    :param new_variables: A dictionary containing key-value pairs to be
      compared.
    :param old_variables: A dictionary against which 'new_variables' are
      compared.
    :return: True if all key-value pairs in 'new_variables' match their
      counterparts in 'old_variables', False if at least one mismatch is found.
    """
    if not isinstance(new_variables, dict) or not isinstance(
        old_variables, dict
    ):
        raise ValueError(
            "Both new_variables and old_variables must be dictionaries.")

    for key, value in new_variables.items():
        if key in old_variables:
            if old_variables[key] != value:
                return False
    return True
