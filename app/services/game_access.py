from typing import Any

from app.core.exceptions import ForbiddenError, NotFoundError


def can_access_user(
    user: Any,
    *,
    api_key: str | None = None,
    oauth_user_id: str | None = None,
    is_admin: bool = False,
) -> bool:
    """
    Return whether the caller context is allowed to access a user.

    Admin tokens can access every user. API-key callers are scoped to users
    created with their key. OAuth non-admin callers pass through here so that
    game-level enforcement (get_authorized_game) gates individual data points.
    """
    if is_admin:
        return True

    if api_key and getattr(user, "apiKey_used", None) == api_key:
        return True

    # Users don't store oauth_user_id; OAuth non-admin scope is enforced at
    # game level within the calling service method.
    if oauth_user_id and not api_key:
        return True

    return False


async def get_authorized_user(
    user_repository,
    external_user_id: str,
    *,
    api_key: str | None = None,
    oauth_user_id: str | None = None,
    is_admin: bool = False,
) -> Any:
    user = await user_repository.read_by_column(
        "externalUserId", external_user_id, not_found_raise_exception=True
    )
    if not can_access_user(
        user,
        api_key=api_key,
        oauth_user_id=oauth_user_id,
        is_admin=is_admin,
    ):
        raise ForbiddenError(detail="You do not have permission to access this user")
    return user


def can_access_game(
    game: Any,
    *,
    api_key: str | None = None,
    oauth_user_id: str | None = None,
    is_admin: bool = False,
) -> bool:
    """
    Return whether the caller context is allowed to access a game.

    Admin bearer tokens can access every game. Non-admin callers are scoped to
    games created with their API key prefix or their OAuth subject.
    """
    if is_admin:
        return True

    if api_key and getattr(game, "apiKey_used", None) == api_key:
        return True

    if oauth_user_id and getattr(game, "oauth_user_id", None) == oauth_user_id:
        return True

    return False


async def get_authorized_game(
    game_repository,
    game_id,
    *,
    api_key: str | None = None,
    oauth_user_id: str | None = None,
    is_admin: bool = False,
) -> Any:
    game = await game_repository.read_by_id(
        game_id,
        not_found_raise_exception=False,
    )
    if not game:
        raise NotFoundError(detail=f"Game not found by gameId: {game_id}")

    if not can_access_game(
        game,
        api_key=api_key,
        oauth_user_id=oauth_user_id,
        is_admin=is_admin,
    ):
        raise ForbiddenError(detail="You do not have permission to access this game")

    return game
