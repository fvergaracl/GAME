from pydantic import BaseModel, Field


class OAuthUserBase(BaseModel):
    """
    Canonical OAuth user linkage schema.

    Represents a user identity synchronized from an external OAuth provider
    (for example Keycloak), including request attribution fields.

    Attributes:
        provider (str): OAuth provider name.
        provider_user_id (str): Stable subject/identifier from the provider.
        status (str): Current status of the OAuth-linked user record.
        apiKey_used (str): API key used in the originating request context.
        oauth_user_id (str): OAuth subject that performed the operation.
    """

    provider: str = Field(
        ...,
        description="OAuth provider identifier.",
        example="keycloak",
    )
    provider_user_id: str = Field(
        ...,
        description="Unique user identifier provided by the OAuth provider.",
        example="3c95c2d7-1ce8-4ea0-b35f-6dfd19127f35",
    )
    status: str = Field(
        ...,
        description="Lifecycle status of the OAuth user record.",
        example="active",
    )
    apiKey_used: str = Field(
        ...,
        description="API key associated with the request that created/updated this record.",
        example="gk_live_3f6a9e0f1a2b4c5d6e7f8a9b",
    )
    oauth_user_id: str = Field(
        ...,
        description="OAuth subject of the actor who performed the operation.",
        example="3c95c2d7-1ce8-4ea0-b35f-6dfd19127f35",
    )


class CreateOAuthUser(BaseModel):
    """
    Request schema for creating an OAuth-linked user record.

    Attributes:
        provider (str): OAuth provider name.
        provider_user_id (str): Stable user identifier from provider claims.
        status (str): Initial status of the user linkage.
    """

    provider: str = Field(
        ...,
        description="OAuth provider identifier.",
        example="keycloak",
    )
    provider_user_id: str = Field(
        ...,
        description="Unique user identifier from the provider (e.g., `sub`).",
        example="3c95c2d7-1ce8-4ea0-b35f-6dfd19127f35",
    )
    status: str = Field(
        ...,
        description="Initial status of the OAuth user record.",
        example="active",
    )

    @staticmethod
    def example() -> dict:
        """
        Returns a representative payload for OAuth user creation.
        """
        return {
            "provider": "keycloak",
            "provider_user_id": "3c95c2d7-1ce8-4ea0-b35f-6dfd19127f35",
            "status": "active",
        }
