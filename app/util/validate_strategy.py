def validate_strategy(json_data):
    valid_variable_names = [
        "@AVG_POINTS_GAME_BY_USER",
        "@AVG_POINTS_TASK_BY_USER",
        "@LAST_PERSONAL_POINTS_GAME",
        "@LAST_PERSONAL_POINTS_TASK",
    ]

    # Verificar las claves principales
    required_keys = ["label", "description", "tags", "static_variables", "rules"]
    for key in required_keys:
        if key not in json_data:
            raise ValueError(f"Key missing in JSON: {key}")

    # Verificar cada regla en "rules"
    for rule in json_data["rules"]:
        for key in ["name", "description", "conditions", "reward", "priority"]:
            if key not in rule:
                raise ValueError(f"Key missing in rule: {key}")

        # Validar las referencias de variables en condiciones y recompensas
        for condition in rule["conditions"]:
            for variable in valid_variable_names:
                if variable in condition:
                    break
            else:
                raise ValueError(
                    f"Invalid variable reference in condition: {condition}"
                )

        for variable in valid_variable_names:
            if variable in rule["reward"]:
                break
        else:
            raise ValueError(f"Invalid variable reference in reward: {rule['reward']}")

    return True
