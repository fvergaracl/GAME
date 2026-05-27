import json
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from app.repository.export_audit_log_repository import ExportAuditLogRepository
from app.schema.export_schema import (
    ExportDatasetType,
    ExportFilters,
    ExportFormat,
    ExportStatus,
)
from app.services.export_service import DATASET_COLUMNS, ExportService


async def _collect(async_iter):
    out = []
    async for chunk in async_iter:
        out.append(chunk)
    return out


async def _aiter(items):
    for it in items:
        yield it


class TestExportServiceAudit(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.repo = MagicMock(spec=ExportAuditLogRepository)
        self.repo.create = AsyncMock()
        self.repo.mark_finished = AsyncMock()
        self.service = ExportService(export_audit_log_repository=self.repo)

    async def test_audit_start_persists_started_row_with_oauth_user(self):
        filters = ExportFilters(
            externalGameId="g1",
            dateFrom=datetime(2026, 1, 1),
            limit=500,
        )

        await self.service.audit_start(
            dataset_type=ExportDatasetType.USER_POINTS.value,
            export_format=ExportFormat.CSV.value,
            filters=filters,
            oauth_user_id="user-abc",
        )

        self.repo.create.assert_awaited_once()
        payload = self.repo.create.await_args.args[0]
        self.assertEqual(payload.datasetType, "user-points")
        self.assertEqual(payload.format, "csv")
        self.assertEqual(payload.status, ExportStatus.STARTED.value)
        self.assertEqual(payload.rowLimit, 500)
        self.assertEqual(payload.rowCount, -1)
        self.assertEqual(payload.oauth_user_id, "user-abc")
        self.assertEqual(payload.requestedBy, "user-abc")
        self.assertEqual(payload.filters["externalGameId"], "g1")
        self.assertIn("dateFrom", payload.filters)

    async def test_audit_start_falls_back_to_api_key_when_no_oauth(self):
        filters = ExportFilters(limit=100)

        await self.service.audit_start(
            dataset_type=ExportDatasetType.USERS.value,
            export_format=ExportFormat.JSON.value,
            filters=filters,
            api_key="gme_live_xyz",
        )

        payload = self.repo.create.await_args.args[0]
        self.assertEqual(payload.requestedBy, "gme_live_xyz")
        self.assertEqual(payload.apiKey_used, "gme_live_xyz")
        self.assertIsNone(payload.oauth_user_id)

    async def test_audit_start_sets_created_at_explicitly(self):
        # BaseModel declares server_default=func.now() but the project's
        # migrations create the column nullable with no DB default. Without
        # an explicit timestamp, audit rows land with NULL created_at and
        # the dataset/created_at index becomes useless for filtering.
        before = datetime.now(timezone.utc)
        await self.service.audit_start(
            dataset_type=ExportDatasetType.USERS.value,
            export_format=ExportFormat.CSV.value,
            filters=ExportFilters(limit=10),
            oauth_user_id="user-x",
        )
        after = datetime.now(timezone.utc)
        payload = self.repo.create.await_args.args[0]
        self.assertIsNotNone(payload.created_at)
        self.assertEqual(payload.created_at.tzinfo, timezone.utc)
        self.assertGreaterEqual(payload.created_at, before)
        self.assertLessEqual(payload.created_at, after)

    async def test_audit_finish_updates_row(self):
        await self.service.audit_finish(
            "audit-id-1",
            row_count=42,
            status=ExportStatus.COMPLETED.value,
        )
        self.repo.mark_finished.assert_awaited_once_with(
            "audit-id-1",
            row_count=42,
            status=ExportStatus.COMPLETED.value,
        )


class TestExportServiceFormatters(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.repo = MagicMock(spec=ExportAuditLogRepository)
        self.service = ExportService(export_audit_log_repository=self.repo)

    async def test_csv_emits_header_and_rows(self):
        columns = DATASET_COLUMNS[ExportDatasetType.USERS.value]
        rows = [
            {
                "id": "u1",
                "externalUserId": "ext-1",
                "created_at": "2026-01-01T00:00:00",
                "updated_at": "2026-01-02T00:00:00",
                "apiKey_used": "gme_live_a",
                "oauth_user_id": None,
            },
            {
                "id": "u2",
                "externalUserId": "ext-2",
                "created_at": "2026-01-03T00:00:00",
                "updated_at": "2026-01-04T00:00:00",
                "apiKey_used": None,
                "oauth_user_id": "sub-2",
            },
        ]
        chunks = await _collect(
            ExportService.format_as_csv(_aiter(rows), columns)
        )
        body = b"".join(chunks).decode("utf-8")
        lines = [line for line in body.splitlines() if line]
        self.assertEqual(lines[0], ",".join(columns))
        self.assertIn("ext-1", lines[1])
        self.assertIn("ext-2", lines[2])
        # None values become empty strings, not literal "None".
        self.assertNotIn("None", body)

    async def test_csv_serializes_dict_cells_as_json(self):
        columns = ["id", "data"]
        rows = [{"id": "x", "data": {"k": 1, "v": "abc"}}]
        chunks = await _collect(
            ExportService.format_as_csv(_aiter(rows), columns)
        )
        body = b"".join(chunks).decode("utf-8")
        # The data cell is a JSON-encoded dict, quoted by csv module.
        self.assertIn('"{""k"":1,""v"":""abc""}"', body)

    async def test_json_emits_valid_array(self):
        rows = [{"id": "1", "name": "a"}, {"id": "2", "name": "b"}]
        chunks = await _collect(ExportService.format_as_json(_aiter(rows)))
        body = b"".join(chunks).decode("utf-8")
        parsed = json.loads(body)
        self.assertEqual(parsed, rows)

    async def test_json_emits_empty_array_when_no_rows(self):
        chunks = await _collect(ExportService.format_as_json(_aiter([])))
        body = b"".join(chunks).decode("utf-8")
        self.assertEqual(json.loads(body), [])

    async def test_format_iterator_routes_to_csv_for_csv_format(self):
        rows = [{"id": "u1", "externalUserId": "x"}]
        gen = self.service.format_iterator(
            ExportDatasetType.USERS.value,
            ExportFormat.CSV.value,
            _aiter(rows),
        )
        chunks = await _collect(gen)
        body = b"".join(chunks).decode("utf-8")
        self.assertIn("externalUserId", body.splitlines()[0])

    async def test_format_iterator_routes_to_json_for_json_format(self):
        rows = [{"id": "u1"}]
        gen = self.service.format_iterator(
            ExportDatasetType.USERS.value,
            ExportFormat.JSON.value,
            _aiter(rows),
        )
        body = b"".join(await _collect(gen)).decode("utf-8")
        self.assertEqual(json.loads(body), rows)

    def test_media_type_for_csv(self):
        self.assertIn(
            "text/csv", ExportService.media_type_for(ExportFormat.CSV.value)
        )

    def test_media_type_for_xlsx(self):
        self.assertIn(
            "spreadsheetml",
            ExportService.media_type_for(ExportFormat.XLSX.value),
        )

    def test_filename_for_includes_dataset_and_extension(self):
        name = ExportService.filename_for(
            ExportDatasetType.USER_POINTS.value, ExportFormat.CSV.value
        )
        self.assertTrue(name.startswith("user-points_"))
        self.assertTrue(name.endswith(".csv"))


class TestExportServiceIterators(unittest.IsolatedAsyncioTestCase):
    """
    Iterator-level tests that snapshot the compiled SQL and the keys each
    iterator yields. These exist because S1 shipped with
    iter_user_interactions targeting a non-existent ``userinteractions``
    table — a bug that bypassed all existing tests (which mock the iterator)
    and only surfaced via a manual smoke test against Postgres.
    """

    def setUp(self):
        self.repo = MagicMock(spec=ExportAuditLogRepository)
        self.service = ExportService(export_audit_log_repository=self.repo)

    async def _exercise(self, iterator_factory, fake_row):
        """
        Replace _stream_rows so we (a) capture the SQLAlchemy statement and
        (b) feed a single fake row through the iterator without touching the
        DB. Returns (compiled_sql_lowercase, yielded_dict).
        """
        captured = {}

        async def _fake_stream_rows(_self, stmt):
            captured["stmt"] = stmt
            yield fake_row

        with patch.object(
            ExportService, "_stream_rows", _fake_stream_rows
        ):
            rows = []
            async for row in iterator_factory():
                rows.append(row)
        compiled = str(
            captured["stmt"].compile(compile_kwargs={"literal_binds": True})
        ).lower()
        return compiled, rows[0]

    async def test_iter_user_interactions_queries_useractions_table(self):
        # The key regression check: must hit `useractions`, never
        # `userinteractions` (which doesn't exist in the DB).
        fake = SimpleNamespace(
            id="a-1",
            created_at=datetime(2026, 5, 1, 12, 0, 0),
            externalUserId="ext-u-1",
            typeAction="task_completed",
            description="user completed task",
            data={"taskId": "t-1"},
            apiKey_used="gme_live_abc",
        )
        sql, row = await self._exercise(
            lambda: self.service.iter_user_interactions(
                ExportFilters(limit=10)
            ),
            fake,
        )
        self.assertIn("useractions", sql)
        self.assertNotIn("userinteractions", sql)
        self.assertEqual(
            set(row.keys()),
            set(DATASET_COLUMNS[ExportDatasetType.USER_INTERACTIONS.value]),
        )

    async def test_iter_users_yields_columns_matching_dataset_columns(self):
        fake = SimpleNamespace(
            id="u-1",
            externalUserId="ext-u-1",
            created_at=datetime(2026, 5, 1),
            updated_at=datetime(2026, 5, 2),
            apiKey_used=None,
            oauth_user_id="sub-1",
        )
        _, row = await self._exercise(
            lambda: self.service.iter_users(ExportFilters(limit=10)),
            fake,
        )
        self.assertEqual(
            set(row.keys()),
            set(DATASET_COLUMNS[ExportDatasetType.USERS.value]),
        )

    async def test_iter_user_points_yields_columns_matching_dataset_columns(
        self,
    ):
        fake = SimpleNamespace(
            id="p-1",
            created_at=datetime(2026, 5, 1),
            externalUserId="ext-u-1",
            externalTaskId="ext-t-1",
            externalGameId="ext-g-1",
            points=10,
            caseName="default",
            description="",
            idempotencyKey="key-1",
            data={},
            apiKey_used=None,
        )
        _, row = await self._exercise(
            lambda: self.service.iter_user_points(ExportFilters(limit=10)),
            fake,
        )
        self.assertEqual(
            set(row.keys()),
            set(DATASET_COLUMNS[ExportDatasetType.USER_POINTS.value]),
        )

    async def test_iter_wallet_transactions_yields_columns_matching_columns(
        self,
    ):
        fake = SimpleNamespace(
            id="w-1",
            created_at=datetime(2026, 5, 1),
            externalUserId="ext-u-1",
            transactionType="credit",
            points=5,
            coins=1,
            appliedConversionRate=5.0,
            data={},
            apiKey_used=None,
        )
        _, row = await self._exercise(
            lambda: self.service.iter_wallet_transactions(
                ExportFilters(limit=10)
            ),
            fake,
        )
        self.assertEqual(
            set(row.keys()),
            set(DATASET_COLUMNS[
                ExportDatasetType.WALLET_TRANSACTIONS.value
            ]),
        )


if __name__ == "__main__":
    unittest.main()
