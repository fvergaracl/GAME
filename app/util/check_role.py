from typing import Any, Mapping


def check_role(
    token_decoded: Mapping[str, Any] | None, required_role: str | None
) -> bool:
    """
    Determine whether a decoded JWT contains the required role.

    Semantics (aligned with strict Keycloak usage + defensive safety):

    - Accepts only dict-like tokens; anything else -> False
    - Empty / None role -> False
    - Checks in order:
        1) realm_access.roles (Keycloak global roles)
        2) top-level "roles" (custom mapped tokens)
        3) resource_access["account"].roles (client roles ONLY for 'account')
    - Ignores roles from other clients (prevents privilege bleed)

    This function is idempotent, side-effect free, and safe against malformed
      tokens.
    """

    if not isinstance(token_decoded, Mapping):
        return False

    if not isinstance(required_role, str) or not required_role.strip():
        return False

    realm_access = token_decoded.get("realm_access")
    if isinstance(realm_access, Mapping):
        realm_roles = realm_access.get("roles")
        if isinstance(
            realm_roles, (list, tuple, set)
        ) and required_role in realm_roles:
            return True

    roles = token_decoded.get("roles")
    if isinstance(roles, (list, tuple, set)) and required_role in roles:
        return True

    resource_access = token_decoded.get("resource_access")
    if not isinstance(resource_access, Mapping):
        return False

    account = resource_access.get("account")
    if not isinstance(account, Mapping):
        return False

    account_roles = account.get("roles")
    if isinstance(
        account_roles, (list, tuple, set)
    ) and required_role in account_roles:
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
