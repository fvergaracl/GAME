from datetime import datetime
from uuid import UUID


def serialize_wallet(wallet):
    """
    Serializes a Wallet instance to a dictionary, converting UUIDs to strings.

    Args:
        wallet (Wallet): The wallet instance to be serialized.

    Returns:
        dict: A dictionary representation of the wallet instance with UUIDs as
          strings.
    """
    wallet_dict = wallet.__dict__
    for key, value in wallet_dict.items():
        if isinstance(value, UUID):
            wallet_dict[key] = str(value)
        elif isinstance(value, datetime):
            wallet_dict[key] = value.isoformat()

    cleaned_dict = {
        key: value
        for key, value in wallet_dict.items()
        if not key.startswith("_")  # Skip internal attributes
    }
    return cleaned_dict
