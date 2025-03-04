def check_role(token_decoded, role) -> bool:
    """
    Check if the user has the required role.

    Args:
        token_decoded (dict): The decoded token.
        role (str): The role required.

    Returns:
        bool: True if the user has the required role, False otherwise.
    """
    if not isinstance(token_decoded, dict):
        return False
    if not role:
        return False

    resource_access = token_decoded.get("resource_access", {})
    account_access = resource_access.get("account", {})
    roles = account_access.get("roles", [])

    if role not in roles:
        return False

    return True
