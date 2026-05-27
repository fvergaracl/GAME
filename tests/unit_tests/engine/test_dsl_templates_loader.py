"""
Unit tests for the user-template loader (Sprint 8).

The loader is intentionally simple: read every JSON in
``app/engine/dsl_templates/user/``, validate the AST, freeze the result
in a module-global cache. These tests pin three things:

  * Every shipped template parses and AST-validates.
  * Each template carries the full schema (id, name, blocklyXml, AST).
  * The cache is honoured on the second call (the on-disk files are
    static; re-reading them on every request would be wasted I/O).
  * The DSL_EXTEND template references an existing built-in parent
    ('default') — the editor would otherwise show a broken card.
"""

import json

import pytest

from app.engine.dsl_templates import loader as templates_loader
from app.engine.dsl_validator import validate_ast
from app.model.strategy_definition import StrategyDefinitionType


@pytest.fixture(autouse=True)
def _clear_cache():
    """Each test starts with a fresh cache so reordering tests can't
    hide a caching bug."""
    templates_loader.reset_cache_for_tests()
    yield
    templates_loader.reset_cache_for_tests()


def test_loader_returns_all_shipped_templates():
    templates = templates_loader.load_user_templates()
    ids = {t.id for t in templates}
    # Sprint 8 ships exactly four user-facing templates. Adding new ones
    # is fine — this assertion just ensures none of the originals were
    # accidentally deleted or renamed.
    assert {
        "engagement_basico",
        "recompensa_completar_tarea",
        "bonus_por_velocidad",
        "bonus_extiende_default",
    } <= ids


def test_each_template_carries_full_schema():
    templates = templates_loader.load_user_templates()
    assert len(templates) >= 4
    for t in templates:
        assert t.id, "template id must be non-empty"
        assert t.name, "template name must be non-empty"
        assert t.astJson, "template astJson must be non-empty"
        assert t.blocklyXml, (
            "template blocklyXml must be non-empty — without it the "
            "editor cannot display the template visually"
        )
        # AST validates standalone (the loader already does this on first
        # load, but we re-check to lock in the contract).
        validate_ast(t.astJson)


def test_dsl_extend_template_references_known_parent_shape():
    """Shape-only check: the DSL_EXTEND template must set parentStrategyId.

    A 'default' parent is the only one currently shipped in the registry
    — the runtime resolution is verified separately by the endpoint
    test ``test_import_dsl_extend_validates_parent``.
    """
    templates = templates_loader.load_user_templates()
    extend = next(t for t in templates if t.id == "bonus_extiende_default")
    assert extend.type == StrategyDefinitionType.DSL_EXTEND
    assert extend.parentStrategyId == "default"


def test_loader_caches_after_first_call(monkeypatch):
    """Second call must hit the cache, not the disk again.

    Implementation detail (the cache) is worth pinning because the
    endpoint hits the loader once per request — a regression turning
    this into per-request disk I/O would be a silent perf bug.
    """
    templates_loader.load_user_templates()

    def boom(*args, **kwargs):
        raise AssertionError("Loader walked the directory twice")

    monkeypatch.setattr(templates_loader, "_scan_templates_dir", boom)
    # Should return the cached list without invoking the scanner.
    second = templates_loader.load_user_templates()
    assert len(second) >= 4


def test_loader_skips_migration_fixtures(tmp_path, monkeypatch):
    """The S5 paridad fixtures live in dsl_templates/ (not user/) on
    purpose. Loader must scan only the user/ subdir so they don't leak
    into the editor's picker.
    """
    # Build a fake user/ directory with one valid template, and a
    # sibling JSON outside it that the loader must ignore.
    fake_user_dir = tmp_path / "user"
    fake_user_dir.mkdir()
    valid = {
        "id": "fake_engagement",
        "name": "Fake",
        "description": "test",
        "type": "DSL_FULL",
        "parentStrategyId": None,
        "astJson": {
            "type": "program",
            "id": "program",
            "rules": [
                {
                    "type": "rule",
                    "id": "r1",
                    "when": {
                        "type": "compare",
                        "id": "c1",
                        "op": "<",
                        "left": {
                            "type": "field",
                            "id": "f1",
                            "path": "user.measurements_count",
                        },
                        "right": {"type": "literal", "id": "l1", "value": 1},
                    },
                    "then": [
                        {
                            "type": "assign_points",
                            "id": "a1",
                            "value": {
                                "type": "literal",
                                "id": "l2",
                                "value": 1,
                            },
                            "case_name": "Test",
                        }
                    ],
                }
            ],
        },
        "blocklyXml": "<xml></xml>",
    }
    (fake_user_dir / "good.json").write_text(json.dumps(valid))
    # Sibling outside user/ must NOT be picked up.
    (tmp_path / "should_not_load.json").write_text(json.dumps(valid))

    monkeypatch.setattr(templates_loader, "_TEMPLATES_DIR", fake_user_dir)
    templates_loader.reset_cache_for_tests()

    templates = templates_loader.load_user_templates()
    assert [t.id for t in templates] == ["fake_engagement"]
