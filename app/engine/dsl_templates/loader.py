"""
Loader for user-facing strategy templates.

Templates live as JSON files inside ``app/engine/dsl_templates/user/``
and seed the "Usar una plantilla" CTA in the Blockly editor. Each file
matches the :class:`StrategyTemplateRead` schema (id, name, description,
type, parentStrategyId, astJson, blocklyXml) so the API can return them
verbatim.

Boot semantics:
    * The loader caches the parsed list in a module-global. First call
      walks the directory, validates every AST, and freezes the cache.
    * Validation runs through ``dsl_validator.validate_ast`` - a broken
      template raises at boot time instead of poisoning the editor.
    * The fixtures under ``dsl_templates/`` (``default_v0_0_2.json``,
      ``constant_effort_v0_0_1.json``) are S5 paridad artefacts, not
      user-facing templates; we deliberately scan ONLY the ``user/``
      subdirectory so those stay out of the picker.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from app.engine.dsl_validator import validate_ast
from app.schema.strategy_definition_schema import StrategyTemplateRead

_TEMPLATES_DIR = Path(__file__).parent / "user"
_CACHE: Optional[List[StrategyTemplateRead]] = None


def load_user_templates() -> List[StrategyTemplateRead]:
    """Return the cached list of user-facing templates, loading on first call.

    Each template's ``astJson`` is run through ``validate_ast`` before
    being added to the cache. A failure here is intentional and loud -
    we'd rather fail boot than serve a malformed template that the
    designer would only discover when "Guardar" rejects it.
    """
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    _CACHE = _scan_templates_dir(_TEMPLATES_DIR)
    return _CACHE


def reset_cache_for_tests() -> None:
    """Clear the in-memory cache; only used by tests."""
    global _CACHE
    _CACHE = None


def _scan_templates_dir(directory: Path) -> List[StrategyTemplateRead]:
    """
    Load and validate every JSON strategy template in a directory.

    Each ``*.json`` file is parsed, validated against
    :class:`StrategyTemplateRead`, and its embedded AST is checked with
    ``validate_ast`` so only round-trippable templates are returned. A missing
    directory yields an empty list.

    Args:
        directory (Path): Directory to scan for template files.

    Returns:
        List[StrategyTemplateRead]: Validated templates, sorted by filename.
    """
    if not directory.exists():
        return []
    templates: List[StrategyTemplateRead] = []
    for path in sorted(directory.glob("*.json")):
        with path.open("r", encoding="utf-8") as fh:
            raw = json.load(fh)
        template = StrategyTemplateRead.model_validate(raw)
        validate_ast(template.astJson)
        templates.append(template)
    return templates
