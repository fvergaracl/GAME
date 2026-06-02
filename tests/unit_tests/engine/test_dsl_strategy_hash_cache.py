"""
Sprint 13 — the AST idempotency hash is memoised by ``(id, version)`` for
PUBLISHED definitions so ``DslStrategy.__init__`` doesn't re-hash the same
multi-KB AST on every scoring call. Drafts (whose ``(id, version)`` key is
not stable — edits patch in place) always recompute.
"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from app.engine import dsl_strategy
from app.engine.dsl_interpreter import DslInterpreter
from app.engine.dsl_strategy import DslStrategy, _compute_ast_hash
from app.schema.strategy_definition_schema import StrategyDefinitionRead


def _read(astJson, *, status="PUBLISHED", version=2, id="hc-1"):
    return StrategyDefinitionRead(
        id=id,
        realmId="realm-a",
        name="custom-1",
        description=None,
        type="DSL_FULL",
        parentStrategyId=None,
        astJson=astJson,
        blocklyXml=None,
        version=version,
        status=status,
        createdBy=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        publishedAt=datetime.now(timezone.utc),
        experimentTag=None,
    )


def _ast(value):
    return {
        "type": "program",
        "id": "p",
        "rules": [
            {
                "type": "rule",
                "id": "r1",
                "when": {"type": "literal", "id": "lt", "value": True},
                "then": [
                    {
                        "type": "assign_points",
                        "id": "a1",
                        "value": {
                            "type": "literal", "id": "lv", "value": value,
                        },
                        "case_name": "C",
                    }
                ],
            },
        ],
    }


def _make(definition):
    return DslStrategy(
        definition=definition,
        interpreter=DslInterpreter(max_nodes=100, max_depth=8),
        analytics_service=None,
    )


class TestPublishedHashCache(unittest.TestCase):
    def setUp(self):
        dsl_strategy._PUBLISHED_HASH_CACHE.clear()

    def tearDown(self):
        dsl_strategy._PUBLISHED_HASH_CACHE.clear()

    def test_published_hash_is_cached_by_id_and_version(self):
        ast = _ast(7)
        s1 = _make(_read(ast))
        self.assertEqual(s1.hash_version, _compute_ast_hash(ast))
        self.assertIn(("hc-1", 2), dsl_strategy._PUBLISHED_HASH_CACHE)

        # A second instance for the same (id, version) is served from the
        # cache: even a *different* AST returns the first cached hash,
        # proving the lookup keys on (id, version) and never re-hashes.
        # (In production a published row is immutable, so this collision
        # can't happen — the test forces it to observe the cache hit.)
        s2 = _make(_read(_ast(999)))
        self.assertEqual(s2.hash_version, s1.hash_version)

    def test_draft_is_never_cached_and_always_recomputes(self):
        ast = _ast(7)
        s1 = _make(_read(ast, status="DRAFT"))
        self.assertEqual(s1.hash_version, _compute_ast_hash(ast))
        self.assertNotIn(("hc-1", 2), dsl_strategy._PUBLISHED_HASH_CACHE)

        # Editing a draft in place (same id/version, new AST) yields a
        # fresh hash — drafts are not memoised.
        s2 = _make(_read(_ast(999), status="DRAFT"))
        self.assertNotEqual(s2.hash_version, s1.hash_version)
        self.assertEqual(s2.hash_version, _compute_ast_hash(_ast(999)))

    def test_different_versions_get_distinct_entries(self):
        _make(_read(_ast(1), version=2))
        _make(_read(_ast(2), version=3))
        self.assertIn(("hc-1", 2), dsl_strategy._PUBLISHED_HASH_CACHE)
        self.assertIn(("hc-1", 3), dsl_strategy._PUBLISHED_HASH_CACHE)

    def test_cache_is_bounded(self):
        original = dsl_strategy._PUBLISHED_HASH_CACHE_MAXSIZE
        dsl_strategy._PUBLISHED_HASH_CACHE_MAXSIZE = 3
        try:
            for v in range(10):
                _make(_read(_ast(v), version=v))
            self.assertLessEqual(
                len(dsl_strategy._PUBLISHED_HASH_CACHE), 3
            )
        finally:
            dsl_strategy._PUBLISHED_HASH_CACHE_MAXSIZE = original


if __name__ == "__main__":
    unittest.main()
