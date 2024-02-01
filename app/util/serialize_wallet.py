# Convert the Wallet instance to a dictionary for serialization,
# Ensuring all UUID values are also converted to strings.
from uuid import UUID
from datetime import datetime


def serialize_wallet(wallet):
    wallet_dict = wallet.__dict__
    for key, value in wallet_dict.items():
        if isinstance(value, UUID):
            wallet_dict[key] = str(value)
        elif isinstance(value, datetime):
            wallet_dict[key] = value.isoformat()

    cleaned_dict = {
        key: value
        for key, value in wallet_dict.items()
        if not key.startswith('_')  # Skip internal attributes
    }
    return cleaned_dict
