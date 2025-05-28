def check_role(token_decoded: dict, required_role: str) -> bool:
    """
    Check if the given decoded JWT token contains the required role.

    This function verifies whether a specific role is present in the decoded token,
    checking both the top-level `roles` claim (commonly used when roles are mapped directly)
    and within the `resource_access` section (when roles are assigned per client).

    Args:
        token_decoded (dict): The decoded JWT token as a dictionary.
        required_role (str): The role to verify against the token.

    Returns:
        bool: True if the required role is present, False otherwise.

    Example:
        >>> check_role(token, "AdministratorGAME")
        True
    """

    # Check direct roles field (custom mapped in token)
    roles = token_decoded.get("roles", [])
    if isinstance(roles, list) and required_role in roles:
        return True

    # Check client-specific roles under resource_access
    resource_access = token_decoded.get("resource_access", {})
    if isinstance(resource_access, dict):
        for client, access in resource_access.items():
            client_roles = access.get("roles", [])
            if isinstance(client_roles, list) and required_role in client_roles:
                return True

    return False

# Example usage:
# token_decoded = {
#     "roles": ["User", "AdministratorGAME"],
#     "resource_access": {
#         "game_client": {
#             "roles": ["User", "AdministratorGAME"]
#         },
#         "another_client": {
#             "roles": ["User"]
#         }
#     }
# }
# print(check_role(token_decoded, "AdministratorGAME"))  # Output: True
#     raise ForbiddenError("You don't have permission to create API key")
#     )
#     return await service_api_key.get_all_api_keys(api_key, oauth_user_id)
#     await service_api_key.get_all_api_keys(api_key, oauth_user_id)
