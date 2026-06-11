from typing import Any, Optional
from uuid import UUID

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.engine.all_engine_strategies import all_engine_strategies
from app.model.strategy_definition import StrategyDefinitionStatus
from app.repository.game_params_repository import GameParamsRepository
from app.repository.game_repository import GameRepository
from app.repository.task_params_repository import TaskParamsRepository
from app.repository.task_repository import TaskRepository
from app.repository.user_points_repository import UserPointsRepository
from app.repository.user_repository import UserRepository
from app.schema.task_schema import (CreateTask, CreateTaskPost,
                                    CreateTaskPostSuccesfullyCreated, FindTask,
                                    PatchTask, ResponseDeleteTask, ResponsePatchTask)
from app.schema.tasks_params_schema import (CreateTaskParams, InsertTaskParams,
                                            UpdateTaskParams)
from app.services.base_service import BaseService
from app.services.game_access import get_authorized_game
from app.services.strategy_definition_service import StrategyDefinitionService
from app.services.strategy_service import (StrategyService, is_custom_strategy_id,
                                           parse_custom_strategy_id, resolve_realm_id)


class TaskService(BaseService):
    """
    Service class for managing tasks.

    Attributes:
        strategy_service (StrategyService): Service instance for strategies.
        task_repository (TaskRepository): Repository instance for tasks.
        game_repository (GameRepository): Repository instance for games.
        user_repository (UserRepository): Repository instance for users.
        user_points_repository (UserPointsRepository): Repository instance for
          user points.
        game_params_repository (GameParamsRepository): Repository instance for
          game parameters.
        task_params_repository (TaskParamsRepository): Repository instance for
          task parameters.
    """

    def __init__(
        self,
        strategy_service: StrategyService,
        task_repository: TaskRepository,
        game_repository: GameRepository,
        user_repository: UserRepository,
        user_points_repository: UserPointsRepository,
        game_params_repository: GameParamsRepository,
        task_params_repository: TaskParamsRepository,
        strategy_definition_service: Optional[StrategyDefinitionService] = None,
    ) -> None:
        """
        Initializes the TaskService with the provided repositories and
          services.

        ``strategy_definition_service`` is optional so existing call sites
        and tests that don't exercise ``custom:`` strategyIds keep
        working. Required for :meth:`patch_task_by_id` to validate
        ``custom:`` ids against the persistent registry.
        """
        self.strategy_service = strategy_service
        self.task_repository = task_repository
        self.game_repository = game_repository
        self.user_repository = user_repository
        self.user_points_repository = user_points_repository
        self.game_params_repository = game_params_repository
        self.task_params_repository = task_params_repository
        self.strategy_definition_service = strategy_definition_service
        super().__init__(task_repository)

    async def _validate_strategy_assignment(
        self,
        strategy_id: str,
        *,
        api_key: Optional[str] = None,
        oauth_user_id: Optional[str] = None,
    ) -> None:
        """
        Mirror of ``GameService._validate_strategy_assignment``. Kept here
        as a sibling rather than a shared helper to avoid a third
        cross-service import path; the body is small enough that
        duplication is cheaper than the extra abstraction.
        """
        if not is_custom_strategy_id(strategy_id):
            strategies = all_engine_strategies()
            strategy = next((s for s in strategies if s.id == strategy_id), None)
            if not strategy:
                raise NotFoundError(detail=f"Strategy with id: {strategy_id} not found")
            return
        if self.strategy_definition_service is None:
            raise BadRequestError(
                detail=(
                    "Custom strategy assignment is unavailable: "
                    "StrategyDefinitionService not wired."
                )
            )
        realmId = resolve_realm_id(api_key=api_key, oauth_user_id=oauth_user_id)
        uuid_part = parse_custom_strategy_id(strategy_id)
        definition = await self.strategy_definition_service.get_strategy(
            id=uuid_part, realmId=realmId
        )
        if definition.status != StrategyDefinitionStatus.PUBLISHED.value:
            raise BadRequestError(
                detail=(
                    f"Only PUBLISHED custom strategies can be assigned. "
                    f"Strategy '{definition.name}' v{definition.version} "
                    f"is {definition.status}."
                )
            )

    async def patch_task_by_id(
        self,
        gameId: UUID,
        taskId: UUID,
        schema: PatchTask,
        *,
        api_key: Optional[str] = None,
        oauth_user_id: Optional[str] = None,
        is_admin: bool = False,
        enforce_scope: bool = False,
    ) -> ResponsePatchTask:
        """
        Partially update a task identified by ``gameId`` + ``taskId``.

        Mutable fields: ``strategyId``, ``status`` and ``params``. When
        ``params`` is provided it is treated as the desired full set and
        synced via :meth:`_sync_task_params` (update existing rows by id,
        create rows without an id, delete rows omitted from the list);
        omit ``params`` to leave them untouched.

        ``strategyId`` accepts both built-ins and ``custom:<uuid>`` -
        validated by :meth:`_validate_strategy_assignment` with the
        caller's tenant boundary.
        """
        if enforce_scope:
            game = await get_authorized_game(
                self.game_repository,
                gameId,
                api_key=api_key,
                oauth_user_id=oauth_user_id,
                is_admin=is_admin,
            )
        else:
            game = await self.game_repository.read_by_id(
                gameId, not_found_raise_exception=False
            )
        if not game:
            raise NotFoundError(detail=f"Game not found by gameId: {gameId}")

        task = await self.task_repository.read_by_id(
            taskId, not_found_raise_exception=False
        )
        if not task:
            raise NotFoundError(detail=f"Task not found by taskId: {taskId}")
        if str(task.gameId) != str(gameId):
            # Mismatched parent - 404 instead of 400 so we don't leak
            # which other game the task actually belongs to.
            raise NotFoundError(
                detail=(f"Task {taskId} does not belong to game {gameId}.")
            )

        # Build the scalar update payload only with non-None fields the
        # caller actually wants to change. ``params`` is handled separately
        # (synced below) so it doesn't go through ``patch_by_id``.
        update_fields = {}
        if schema.strategyId is not None:
            await self._validate_strategy_assignment(
                schema.strategyId,
                api_key=api_key,
                oauth_user_id=oauth_user_id,
            )
            update_fields["strategyId"] = schema.strategyId
        if schema.status is not None:
            update_fields["status"] = schema.status

        params_provided = schema.params is not None

        # An empty patch (no scalar fields and no params block) is rejected
        # to keep the audit trail meaningful.
        if not update_fields and not params_provided:
            raise ConflictError(detail="Empty patch: no fields provided.")

        # Only the scalar fields that actually differ get written; this also
        # lets us reject a pure no-op field patch (when params aren't touched)
        # without blocking a params-only change.
        changed_fields = {
            k: v for k, v in update_fields.items() if getattr(task, k) != v
        }
        if not changed_fields and not params_provided:
            raise ConflictError(
                detail=(
                    "It is not possible to update the task with the same data"
                )
            )

        if changed_fields:
            task = await self.task_repository.patch_by_id(taskId, changed_fields)

        updated_params = None
        if params_provided:
            updated_params = await self._sync_task_params(
                taskId, schema.params, api_key=api_key
            )

        return ResponsePatchTask(
            taskId=task.id,
            gameId=gameId,
            externalTaskId=task.externalTaskId,
            strategyId=task.strategyId,
            status=task.status,
            taskParams=updated_params,
            message=(f"Task with taskId: {taskId} updated successfully"),
        )

    async def _sync_task_params(
        self,
        taskId: UUID,
        params: list[UpdateTaskParams],
        *,
        api_key: Optional[str] = None,
    ) -> list:
        """
        Reconcile a task's params to the desired set in ``params``.

        For each entry: a present ``id`` matching an existing param updates
        it in place; otherwise a new param is created. Existing params whose
        id is absent from ``params`` are deleted. Values are persisted as
        strings, mirroring task creation. Returns the surviving param rows.
        """
        existing = (
            await self.task_params_repository.read_by_column(
                "taskId",
                taskId,
                not_found_raise_exception=False,
                only_one=False,
            )
            or []
        )
        existing_by_id = {str(p.id): p for p in existing}

        kept_ids = set()
        result = []
        for param in params:
            param_id = getattr(param, "id", None)
            id_str = str(param_id) if param_id is not None else None
            if id_str and id_str in existing_by_id:
                kept_ids.add(id_str)
                patched = await self.task_params_repository.patch_task_params_by_id(
                    param_id,
                    CreateTaskParams(key=param.key, value=str(param.value)),
                )
                result.append(patched)
            else:
                to_insert = InsertTaskParams(
                    key=param.key,
                    value=str(param.value),
                    taskId=str(taskId),
                    apiKey_used=api_key,
                )
                created = await self.task_params_repository.create(to_insert)
                result.append(created)

        for id_str, row in existing_by_id.items():
            if id_str not in kept_ids:
                await self.task_params_repository.delete_by_id(row.id)

        return result

    async def _get_task_in_game(
        self,
        gameId: UUID,
        taskId: UUID,
        *,
        api_key: Optional[str] = None,
        oauth_user_id: Optional[str] = None,
        is_admin: bool = False,
        enforce_scope: bool = False,
    ):
        """
        Resolve a task that must belong to ``gameId``, honouring scope.

        Shared guard for the ``delete``/``duplicate`` task flows
        (and a sibling of the inline checks in :meth:`patch_task_by_id`):
        the game has to exist (and be in the caller's scope when
        ``enforce_scope`` is set), the task has to exist, and it has to be
        a child of that game. A mismatched parent is reported as 404 so we
        don't leak which other game the task actually belongs to.

        Returns the resolved task row.
        """
        if enforce_scope:
            game = await get_authorized_game(
                self.game_repository,
                gameId,
                api_key=api_key,
                oauth_user_id=oauth_user_id,
                is_admin=is_admin,
            )
        else:
            game = await self.game_repository.read_by_id(
                gameId, not_found_raise_exception=False
            )
        if not game:
            raise NotFoundError(detail=f"Game not found by gameId: {gameId}")

        task = await self.task_repository.read_by_id(
            taskId, not_found_raise_exception=False
        )
        if not task:
            raise NotFoundError(detail=f"Task not found by taskId: {taskId}")
        if str(task.gameId) != str(gameId):
            raise NotFoundError(
                detail=(f"Task {taskId} does not belong to game {gameId}.")
            )
        return task

    async def delete_task_by_id(
        self,
        gameId: UUID,
        taskId: UUID,
        *,
        api_key: Optional[str] = None,
        oauth_user_id: Optional[str] = None,
        is_admin: bool = False,
        enforce_scope: bool = False,
    ) -> ResponseDeleteTask:
        """
        Delete a task (and its params/points) identified by
        ``gameId`` + ``taskId``.

        Full-stack addition mirroring
        :meth:`GameService.delete_game_by_id`: the cascade lives in
        :meth:`TaskRepository.delete_task_by_id` so task params and the
        user-points rows that reference the task go before the task row.
        """
        task = await self._get_task_in_game(
            gameId,
            taskId,
            api_key=api_key,
            oauth_user_id=oauth_user_id,
            is_admin=is_admin,
            enforce_scope=enforce_scope,
        )
        await self.task_repository.delete_task_by_id(taskId)
        return ResponseDeleteTask(
            taskId=task.id,
            gameId=gameId,
            externalTaskId=task.externalTaskId,
            message=f"Task with taskId: {taskId} deleted successfully",
        )

    async def duplicate_task(
        self,
        gameId: UUID,
        taskId: UUID,
        externalTaskId: str,
        *,
        api_key: Optional[str] = None,
        oauth_user_id: Optional[str] = None,
        is_admin: bool = False,
        enforce_scope: bool = False,
    ) -> CreateTaskPostSuccesfullyCreated:
        """
        Duplicate a task within the same game under a new
        ``externalTaskId``.

        Deep-copies the source task's strategy and params onto the new
        task. Reuses :meth:`create_task_by_game_id` for the heavy lifting
        (uniqueness check on the new ``externalTaskId``, row + param
        insertion, response shaping) so the duplicate path can't drift
        from normal task creation.
        """
        source = await self._get_task_in_game(
            gameId,
            taskId,
            api_key=api_key,
            oauth_user_id=oauth_user_id,
            is_admin=is_admin,
            enforce_scope=enforce_scope,
        )
        source_params = await self.task_params_repository.read_by_column(
            "taskId", source.id, not_found_raise_exception=False, only_one=False
        )
        copied_params = [
            CreateTaskParams(key=param.key, value=param.value)
            for param in (source_params or [])
        ]
        create_query = CreateTaskPost(
            externalTaskId=externalTaskId,
            strategyId=source.strategyId,
            params=copied_params or None,
        )
        return await self.create_task_by_game_id(
            gameId,
            create_query,
            api_key,
            oauth_user_id=oauth_user_id,
            is_admin=is_admin,
            enforce_scope=enforce_scope,
        )

    async def get_tasks_list_by_externalGameId(
        self, externalGameId, find_query
    ) -> dict[str, Any]:
        """
        Retrieves a list of tasks associated with a game by its external game
          ID.

        Args:
            externalGameId (str): The external game ID.
            find_query: The query for finding tasks.

        Returns:
            list: A list of tasks associated with the game.
        """
        game = await self.game_repository.read_by_column(
            "externalGameId",
            externalGameId,
            not_found_message=f"Game not found with externalGameId: "
            f"{externalGameId}",
        )

        if not game:
            raise NotFoundError(f"Game not found with externalGameId: {externalGameId}")

        return await self.get_tasks_list_by_gameId(game.id, find_query)

    async def get_tasks_list_by_gameId(
        self,
        gameId,
        find_query,
        *,
        api_key: str = None,
        oauth_user_id: str = None,
        is_admin: bool = False,
        enforce_scope: bool = False,
    ) -> dict[str, Any]:
        """
        Retrieves a list of tasks associated with a game by its game ID.

        Args:
            gameId (UUID): The game ID.
            find_query: The query for finding tasks.

        Returns:
            list: A list of tasks associated with the game.
        """
        if enforce_scope:
            game = await get_authorized_game(
                self.game_repository,
                gameId,
                api_key=api_key,
                oauth_user_id=oauth_user_id,
                is_admin=is_admin,
            )
        else:
            game = await self.game_repository.read_by_id(
                gameId, not_found_raise_exception=False
            )

        if not game:
            raise NotFoundError(f"Game not found with gameId: {gameId}")

        find_task_query = FindTask(
            gameId=game.id, **find_query.model_dump(exclude_none=True)
        )
        all_tasks = await self.task_repository.read_by_gameId(find_task_query)

        strategy_data = self.strategy_service.get_strategy_by_id(game.strategyId)
        game_params = await self.game_params_repository.read_by_column(
            "gameId", game.id, not_found_raise_exception=False, only_one=False
        )
        if game_params:
            for param in game_params:
                if param.key in strategy_data["variables"]:
                    try:
                        param.value = int(param.value)
                    except ValueError:
                        try:
                            param.value = float(param.value)
                        except ValueError:
                            pass
                    type_param = type(param.value)
                    type_strategy_variable = type(strategy_data["variables"][param.key])
                    if type_param == type_strategy_variable:
                        strategy_data["variables"][param.key] = param.value
        cleaned_tasks = []
        for task in all_tasks["items"]:
            strategy_data = self.strategy_service.get_strategy_by_id(task.strategyId)
            task_params = await self.task_params_repository.read_by_column(
                "taskId", task.id, not_found_raise_exception=False, only_one=False
            )
            if game_params:
                for param in game_params:
                    if param.key in strategy_data["variables"]:
                        try:
                            param.value = int(param.value)
                        except ValueError:
                            try:
                                param.value = float(param.value)
                            except ValueError:
                                pass
                        type_param = type(param.value)
                        type_strategy_variable = type(
                            strategy_data["variables"][param.key]
                        )
                        if type_param == type_strategy_variable:
                            strategy_data["variables"][param.key] = param.value

            if task_params:
                for param in task_params:
                    if param.key in strategy_data["variables"]:
                        try:
                            param.value = int(param.value)
                        except ValueError:
                            try:
                                param.value = float(param.value)
                            except ValueError:
                                pass
                        type_param = type(param.value)
                        type_strategy_variable = type(
                            strategy_data["variables"][param.key]
                        )
                        if type_param == type_strategy_variable:
                            strategy_data["variables"][param.key] = param.value
            task_params = task_params if task_params else []
            task_cleaned = task.model_dump()
            task_cleaned["strategy"] = strategy_data
            task_cleaned["gameParams"] = game_params
            task_cleaned["taskParams"] = task_params
            cleaned_tasks.append(task_cleaned)
        all_tasks["items"] = cleaned_tasks
        return all_tasks

    async def get_task_by_gameId_externalTaskId(
        self,
        gameId,
        externalTaskId,
        *,
        api_key: str = None,
        oauth_user_id: str = None,
        is_admin: bool = False,
        enforce_scope: bool = False,
    ) -> CreateTaskPostSuccesfullyCreated:
        """
        Retrieves a task by its game ID and external task ID.

        Args:
            gameId (UUID): The game ID.
            externalTaskId (str): The external task ID.

        Returns:
            CreateTaskPostSuccesfullyCreated: The task details.
        """
        if enforce_scope:
            game = await get_authorized_game(
                self.game_repository,
                gameId,
                api_key=api_key,
                oauth_user_id=oauth_user_id,
                is_admin=is_admin,
            )
        else:
            game = await self.game_repository.read_by_id(
                gameId, not_found_raise_exception=False
            )
        if not game:
            raise NotFoundError(f"Game not found with gameId: {gameId}")

        task = await self.task_repository.read_by_gameId_and_externalTaskId(
            game.id, externalTaskId
        )
        if not task:
            raise NotFoundError(
                f"Task not found with externalTaskId: {externalTaskId} for "
                f"gameId: {gameId}"
            )

        strategy_data = self.strategy_service.get_strategy_by_id(task.strategyId)

        game_params = await self.game_params_repository.read_by_column(
            "gameId", game.id, not_found_raise_exception=False, only_one=False
        )
        if game_params:
            for param in game_params:
                if param.key in strategy_data["variables"]:
                    try:
                        param.value = int(param.value)
                    except ValueError:
                        try:
                            param.value = float(param.value)
                        except ValueError:
                            pass
                    type_param = type(param.value)
                    type_strategy_variable = type(strategy_data["variables"][param.key])
                    if type_param == type_strategy_variable:
                        strategy_data["variables"][param.key] = param.value

        task_params = await self.task_params_repository.read_by_column(
            "taskId", task.id, not_found_raise_exception=False, only_one=False
        )
        if task_params:
            for param in task_params:
                if param.key in strategy_data["variables"]:
                    try:
                        param.value = int(param.value)
                    except ValueError:
                        try:
                            param.value = float(param.value)
                        except ValueError:
                            pass
                    type_param = type(param.value)
                    type_strategy_variable = type(strategy_data["variables"][param.key])
                    if type_param == type_strategy_variable:
                        strategy_data["variables"][param.key] = param.value

        response = CreateTaskPostSuccesfullyCreated(
            externalTaskId=task.externalTaskId,
            externalGameId=game.externalGameId,
            gameParams=game_params,
            taskParams=task_params,
            strategy=strategy_data,
            message=f"Task found successfully with externalTaskId: "
            f"{task.externalTaskId} for gameId: {gameId}",
        )

        return response

    async def get_task_by_externalGameId_externalTaskId(
        self,
        gameId,
        externalTaskId,
        *,
        api_key: str = None,
        oauth_user_id: str = None,
        is_admin: bool = False,
        enforce_scope: bool = False,
    ) -> CreateTaskPostSuccesfullyCreated:
        """
        Retrieves a task by its game ID and external task ID.

        Args:
            gameId (UUID): The game ID.
            externalTaskId (str): The external task ID.

        Returns:
            CreateTaskPostSuccesfullyCreated: The task details.
        """
        game = await self.game_repository.read_by_column(
            "id",
            gameId,
            not_found_message=f"Game not found with id: " f"{gameId}",
            only_one=True,
        )

        return await self.get_task_by_gameId_externalTaskId(
            game.id,
            externalTaskId,
            api_key=api_key,
            oauth_user_id=oauth_user_id,
            is_admin=is_admin,
            enforce_scope=enforce_scope,
        )

    async def create_task_by_externalGameId(
        self, externalGameId, create_query
    ) -> CreateTaskPostSuccesfullyCreated:
        """
        Creates a task for a game by its external game ID.

        Args:
            externalGameId (str): The external game ID.
            create_query: The query for creating the task.

        Returns:
            CreateTaskPostSuccesfullyCreated: The created task details.
        """
        game = await self.game_repository.read_by_column(
            "externalGameId",
            externalGameId,
            not_found_message=f"Game not found with externalGameId: "
            f"{externalGameId}",
            only_one=True,
        )

        return await self.create_task_by_game_id(game.id, externalGameId, create_query)

    async def create_task_by_game_id(
        self,
        gameId,
        create_query,
        api_key: str = None,
        *,
        oauth_user_id: str = None,
        is_admin: bool = False,
        enforce_scope: bool = False,
    ) -> CreateTaskPostSuccesfullyCreated:
        """
        Creates a task for a game by its game ID.

        Args:
            gameId (UUID): The game ID.
            create_query: The query for creating the task.

        Returns:
            CreateTaskPostSuccesfullyCreated: The created task details.
        """
        if enforce_scope:
            game_data = await get_authorized_game(
                self.game_repository,
                gameId,
                api_key=api_key,
                oauth_user_id=oauth_user_id,
                is_admin=is_admin,
            )
        else:
            game_data = await self.game_repository.read_by_id(
                gameId, not_found_raise_exception=False
            )
        if not game_data:
            raise NotFoundError(f"Game not found with gameId: {gameId}")

        task = await self.task_repository.read_by_gameId_and_externalTaskId(
            gameId, create_query.externalTaskId
        )
        if task:
            raise ConflictError(
                f"Task already exists with externalTaskId: "
                f"{create_query.externalTaskId} for gameId: {gameId}"
            )

        strategy_id = create_query.strategyId

        strategy_data = None
        if strategy_id:
            strategy_data = self.strategy_service.get_strategy_by_id(strategy_id)
            if not strategy_data:
                raise NotFoundError(
                    f"Strategy not found with strategyId: {strategy_id}"
                )

        if not strategy_id:
            strategy_id = "default"
        strategy_data = self.strategy_service.get_strategy_by_id(strategy_id)

        strategy_id = str(strategy_id)

        new_task_dict = create_query.model_dump()
        new_task_dict["gameId"] = str(gameId)
        if strategy_id:
            new_task_dict["strategyId"] = str(strategy_id)
        if api_key:
            new_task_dict["apiKey_used"] = api_key
        new_task = CreateTask(**new_task_dict)

        created_task = await self.task_repository.create(new_task)
        created_params = []
        params = create_query.params
        if params:
            del create_query.params

            for param in params:
                params_dict = param.model_dump()
                params_dict["taskId"] = str(created_task.id)
                params_dict["value"] = str(params_dict["value"])
                if api_key:
                    params_dict["apiKey_used"] = api_key
                params_to_insert = InsertTaskParams(**params_dict)
                created_param = await self.task_params_repository.create(
                    params_to_insert
                )
                created_params.append(created_param)

        game_params = await self.game_params_repository.read_by_column(
            "gameId", gameId, not_found_raise_exception=False, only_one=False
        )

        if game_params:
            for param in game_params:
                if param.key in strategy_data["variables"]:
                    try:
                        param.value = int(param.value)
                    except ValueError:
                        try:
                            param.value = float(param.value)
                        except ValueError:
                            pass
                    type_param = type(param.value)
                    type_strategy_variable = type(strategy_data["variables"][param.key])
                    if type_param == type_strategy_variable:
                        strategy_data["variables"][param.key] = param.value

        if created_params:
            for param in created_params:
                if param.key in strategy_data["variables"]:
                    try:
                        param.value = int(param.value)
                    except ValueError:
                        try:
                            param.value = float(param.value)
                        except ValueError:
                            pass
                    type_param = type(param.value)
                    type_strategy_variable = type(strategy_data["variables"][param.key])
                    if type_param == type_strategy_variable:
                        strategy_data["variables"][param.key] = param.value
        externalGameId = game_data.externalGameId
        response = CreateTaskPostSuccesfullyCreated(
            externalTaskId=created_task.externalTaskId,
            externalGameId=externalGameId,
            gameParams=game_params,
            taskParams=created_params,
            strategy=strategy_data,
            message=f"Task created successfully with externalTaskId: "
            f"{created_task.externalTaskId} for gameId: {gameId}",
        )

        return response

    async def get_task_detail_by_id(self, schema) -> dict[str, Any]:
        """
        Retrieves task details by its ID.

        Args:
            schema: The schema containing the task ID.

        Returns:
            dict: The task and strategy details.
        """
        taskId = schema.taskId
        task = await self.task_repository.read_by_id(
            taskId, not_found_message="Task not found by id: {taskId}"
        )
        strategyId = task.strategyId
        strategy = None
        if strategyId:
            strategy = await self.strategy_repository.read_by_id(
                strategyId,
                not_found_message="Strategy not found by id: " f"{strategyId}",
            )
        return {"task": task, "strategy": strategy}

    async def get_points_by_task_id(
        self,
        gameId,
        externalTaskId,
        *,
        api_key: str = None,
        oauth_user_id: str = None,
        is_admin: bool = False,
        enforce_scope: bool = False,
    ) -> Any:
        """
        Retrieves points by task ID.

        Args:
            gameId (UUID): The game ID.
            externalTaskId (str): The external task ID.

        Returns:
            list: A list of points associated with the task.
        """
        if enforce_scope:
            game = await get_authorized_game(
                self.game_repository,
                gameId,
                api_key=api_key,
                oauth_user_id=oauth_user_id,
                is_admin=is_admin,
            )
        else:
            game = await self.game_repository.read_by_column(
                "id",
                gameId,
                not_found_message=f"Game not found with gameId: {gameId}",
                only_one=True,
            )

        task = await self.task_repository.read_by_gameId_and_externalTaskId(
            game.id, externalTaskId
        )
        if not task:
            raise NotFoundError(
                f"Task not found with externalTaskId: {externalTaskId} for "
                f"gameId: {gameId}"
            )

        task_id = task.id

        user_points = await self.user_points_repository.get_all_UserPoints_by_taskId(
            task_id
        )

        return user_points

    async def get_points_of_user_by_task_id(
        self,
        gameId,
        externalTaskId,
        externalUserId,
        *,
        api_key: str = None,
        oauth_user_id: str = None,
        is_admin: bool = False,
        enforce_scope: bool = False,
    ) -> Any:
        """
        Retrieves points of a user by task ID.

        Args:
            gameId (UUID): The game ID.
            externalTaskId (str): The external task ID.
            externalUserId (str): The external user ID.

        Returns:
            dict: The user's points details.
        """
        points_task = await self.get_points_by_task_id_with_details(
            gameId,
            externalTaskId,
            api_key=api_key,
            oauth_user_id=oauth_user_id,
            is_admin=is_admin,
            enforce_scope=enforce_scope,
        )
        user_points = list(
            filter(lambda x: x.externalUserId == externalUserId, points_task)
        )

        if not user_points:
            raise NotFoundError(
                f"User not found with externalUserId: {externalUserId} for "
                f"externalTaskId: {externalTaskId} for gameId: {gameId}"
            )
        return user_points[0]

    async def get_points_by_task_id_with_details(
        self,
        gameId,
        externalTaskId,
        *,
        api_key: str = None,
        oauth_user_id: str = None,
        is_admin: bool = False,
        enforce_scope: bool = False,
    ) -> Any:
        """
        Retrieves points by task ID with details.

        Args:
            gameId (UUID): The game ID.
            externalTaskId (str): The external task ID.

        Returns:
            list: A list of points associated with the task.
        """
        if enforce_scope:
            await get_authorized_game(
                self.game_repository,
                gameId,
                api_key=api_key,
                oauth_user_id=oauth_user_id,
                is_admin=is_admin,
            )

        task = await self.task_repository.read_by_gameId_and_externalTaskId(
            gameId, externalTaskId
        )
        if not task:
            raise NotFoundError(
                f"Task not found with externalTaskId: {externalTaskId} for "
                f"gameId: {gameId}"
            )

        task_id = task.id

        user_points = await self.user_points_repository.get_all_UserPoints_by_taskId_with_details(  # noqa: E501
            task_id
        )
        return user_points

    async def get_task_params_by_externalTaskId(self, externalTaskId) -> Any:
        """
        Retrieves task parameters by external task ID.

        Args:
            externalTaskId (str): The external task ID.

        Returns:
            list: A list of task parameters associated with the task.
        """
        task = await self.task_repository.read_by_column(
            "externalTaskId",
            externalTaskId,
            not_found_message=f"Task not found with externalTaskId: "
            f"{externalTaskId}",
            only_one=True,
        )

        task_id = task.id

        task_params = await self.task_params_repository.read_by_column(
            "taskId",
            task_id,
            not_found_raise_exception=False,
            only_one=False,
        )

        return task_params
