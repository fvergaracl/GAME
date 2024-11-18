from pydantic import BaseModel


class OAuthUserBase(BaseModel):
    """
    Base model for OAuth users
    """

    provider: str
    provider_user_id: str
    status: str
    apiKey_used: str
