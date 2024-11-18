from pydantic import BaseModel


class OAuthUserBase(BaseModel):
    """
    Base model for OAuth users
    """

    provider: str
    provider_user_id: str
    status: str
    apiKey_used: str


class CreateOAuthUser(BaseModel):
    """
    Model for creating an OAuth user
    """

    provider: str
    provider_user_id: str
    status: str
