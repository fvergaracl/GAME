from app.schema.logs_schema import CreateLogs


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
        log_level=log_level, message=message, module=module, details=details
    )
    if api_key:
        log_entry.apiKey_used = api_key
    if oauth_user_id:
        log_entry.oauth_user_id = oauth_user_id
    await service_log.add(log_entry)
