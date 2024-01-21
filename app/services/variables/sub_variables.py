

sub_variables = [
    {
        "name": "#EXTERNAL_USER_ID",
        "type": "string",
        "description": "External user id"
    },
    {
        "name": "#EXTERNAL_TASK_ID",
        "type": "string",
        "description": "External task id"
    },
    {
        "name": "#EXTERNAL_GAME_ID",
        "type": "string",
        "description": "External game id"
    }
]


def get_sub_variables_by_name(name):
    for sub_variable in sub_variables:
        if sub_variable["name"] == name:
            return sub_variable
    return None
