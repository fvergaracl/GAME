from app.core.container import Container
from app.schema.logs_schema import CreateLogs
from app.schema.oauth_users_schema import CreateOAuthUser


async def add_log(
    module, log_level, message, details, service_log, api_key=None, oauth_user_id=None
):
    """
    Helper to add a log entry with apiKey or oauth_user_id if available.

    Args:
        log_level (str): The log level of the log entry.
        message (str): The message of the log entry.
        details (dict): The details of the log entry.
        api_key (str): The API key used to make the request.
        oauthusers_id (str): The OAuth user ID used to make the request.

    """
    log_entry = CreateLogs(
        log_level=log_level,
        message=message,
        module=module,
        details=details,
        apiKey_used=api_key,
        oauth_user_id=oauth_user_id,
    )
    if api_key:
        log_entry.apiKey_used = api_key
    if oauth_user_id:
        log_entry.oauth_user_id = oauth_user_id
    try:
        await service_log.add(log_entry)
    except Exception as e:
        print(f"> Error adding log: {e}")
        oauthusers_service = Container.oauth_users_service()
        create_user = CreateOAuthUser(
            provider="keycloak",
            provider_user_id=oauth_user_id,
            status="active",
        )
        await oauthusers_service.add(create_user)

        return add_log(
            module,
            log_level,
            message,
            details,
            service_log,
            api_key=api_key,
            oauth_user_id=oauth_user_id,
        )
