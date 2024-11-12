from contextlib import AbstractContextManager
from typing import Callable, List, Dict, Union
from sqlalchemy import func, case, String
from sqlalchemy.orm import Session
from app.core.exceptions import BadRequestError
from app.model.games import Games
from app.model.tasks import Tasks
from app.model.users import Users
from app.model.user_points import UserPoints
from app.model.user_actions import UserActions
from app.repository.base_repository import BaseRepository


class DashboardRepository(BaseRepository):
    """
    Repository class for API keys and dashboard metrics.
    """

    def __init__(
        self,
        session_factory: Callable[..., AbstractContextManager[Session]],
        model_games=Games,
        model_tasks=Tasks,
        model_users=Users,
        model_user_points=UserPoints,
        model_user_actions=UserActions,
    ) -> None:
        """
        Initializes the DashboardRepository with the provided session factory and models.
        """
        self.session_factory = session_factory
        self.model_games = model_games
        self.model_tasks = model_tasks
        self.model_users = model_users
        self.model_user_points = model_user_points
        self.model_user_actions = model_user_actions
        super().__init__(session_factory, model_games)

    def process_query(
        self, query, start_date=None, end_date=None, group_by_column=None
    ):
        """
        Processes the query by filtering and grouping the results.

        Args:
            query: The query to process.
            start_date: The start date for the query.
            end_date: The end date for the query.
            group_by_column: The column to group by.

        Returns:
            Any: The processed query.
        """
        if start_date:
            query = query.filter(self.model_users.created_at >= start_date)
        if end_date:
            query = query.filter(self.model_users.created_at <= end_date)
        if group_by_column is not None:
            query = query.group_by(group_by_column)

        return query

    def _get_group_by_column(self, model, group_by: str):
        """
        Returns the appropriate group_by column based on the model and
        grouping criteria.

        Args:
            model: The model to query.
            group_by: The grouping criteria.

        Returns:
            Any: The group_by column.
        """

        if group_by == "day":
            return func.date_trunc("day", model.created_at).label("date")
        elif group_by == "week":
            return case(
                [
                    (
                        func.extract("day", model.created_at).between(1, 7),
                        func.concat("week_1_", func.extract("month", model.created_at)),
                    ),
                    (
                        func.extract("day", model.created_at).between(8, 14),
                        func.concat("week_2_", func.extract("month", model.created_at)),
                    ),
                    (
                        func.extract("day", model.created_at).between(15, 21),
                        func.concat("week_3_", func.extract("month", model.created_at)),
                    ),
                    (
                        func.extract("day", model.created_at).between(22, 28),
                        func.concat("week_4_", func.extract("month", model.created_at)),
                    ),
                    (
                        func.extract("day", model.created_at) >= 29,
                        func.concat("week_5_", func.extract("month", model.created_at)),
                    ),
                ],
                else_="unknown_week",
            ).label("week")
        elif group_by == "month":
            return func.lpad(
                func.cast(func.extract("month", model.created_at), String), 2, "0"
            ).label("month")
        else:
            raise BadRequestError(
                "Invalid group_by value. Choose 'day', 'week', or 'month'."
            )

    def _execute_query(
        self, model, group_by_column, start_date, end_date, aggregation_field
    ) -> List[Dict[str, Union[str, int]]]:
        """Executes a query for a specific model and aggregation field."""
        with self.session_factory() as session:
            query = session.query(group_by_column, aggregation_field.label("count"))
            query = self.process_query(query, start_date, end_date, group_by_column)
            results = query.all()
            return [
                {"label": str(result[0]), "count": result.count} for result in results
            ]

    def get_dashboard_summary(self, start_date, end_date, group_by):
        """
        Retrieves the dashboard summary.

        Args:
            start_date: The start date for the summary.
            end_date: The end date for the summary.
            group_by: The group by for the summary (e.g. day, week, month).

        Returns:
            Dict[str, Any]: The dashboard summary.
        """

        group_by_column_users = self._get_group_by_column(self.model_users, group_by)
        new_users = self._execute_query(
            self.model_users,
            group_by_column_users,
            start_date,
            end_date,
            func.count(self.model_users.id),
        )

        group_by_column_games = self._get_group_by_column(self.model_games, group_by)
        games_opened = self._execute_query(
            self.model_games,
            group_by_column_games,
            start_date,
            end_date,
            func.count(self.model_games.id),
        )

        group_by_column_points = self._get_group_by_column(
            self.model_user_points, group_by
        )
        points_earned = self._execute_query(
            self.model_user_points,
            group_by_column_points,
            start_date,
            end_date,
            func.sum(self.model_user_points.points),
        )

        group_by_column_actions = self._get_group_by_column(
            self.model_user_actions, group_by
        )
        actions_performed = self._execute_query(
            self.model_user_actions,
            group_by_column_actions,
            start_date,
            end_date,
            func.count(self.model_user_actions.id),
        )

        return {
            "new_users": new_users,
            "games_opened": games_opened,
            "points_earned": points_earned,
            "actions_performed": actions_performed,
        }
