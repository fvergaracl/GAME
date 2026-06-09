// Sprint 10: the canonical list of DSL error codes the backend emits.
//
// Kept in sync with ``app/engine/dsl_interpreter.py`` and
// ``app/engine/dsl_validator.py`` and ``app/services/dsl_simulation_service.py``.
// Adding a new code on the backend means:
//   1. Add the code constant here.
//   2. Add an i18n entry under both ``locales/es/errors.json`` and
//      ``locales/en/errors.json``.
// The test suite (``i18n.test.js``) enforces (2) - it iterates this
// array and asserts every code resolves to a non-empty translation in
// both locales.

export const DSL_ERROR_CODES = [
  'DSL_ARITH_DIV_BY_ZERO',
  'DSL_ARITH_OP_NOT_ALLOWED',
  'DSL_ARITH_TYPE_MISMATCH',
  'DSL_ASSIGN_POINTS_NOT_NUMBER',
  'DSL_COMPARE_OP_NOT_ALLOWED',
  'DSL_COMPARE_TYPE_MISMATCH',
  'DSL_FIELD_NOT_PRECOMPUTED',
  'DSL_FIELD_PATH_NOT_ALLOWED',
  'DSL_FUNC_ARITY_MISMATCH',
  'DSL_FUNC_NAME_NOT_ALLOWED',
  'DSL_NO_AST_TO_SIMULATE',
  'DSL_PARENT_FIELD_OUTSIDE_POST',
  'DSL_SET_CASE_NAME_NOT_STRING',
  'DSL_SET_POINTS_NOT_NUMBER',
  'DSL_TIMEOUT',
  'DSL_UNKNOWN_STATEMENT',
]

/**
 * Look up an error code in the ``errors`` namespace. Returns the
 * localised string if a translation exists, or a generic fallback that
 * includes the original English message so the user still sees
 * something actionable.
 */
export function dslErrorMessage(t, code, params, fallbackMessage) {
  if (!code) return fallbackMessage || null
  const key = `errors:${code}`
  // ``t`` returns the key string when nothing is found; we detect that
  // and fall back to the generic ``errors.fallback`` template so the
  // designer never sees the raw code on screen.
  const translated = t(key, { ...params, defaultValue: '' })
  if (translated) return translated
  return t('errors:fallback', {
    message: fallbackMessage || code,
    defaultValue: fallbackMessage || code,
  })
}
