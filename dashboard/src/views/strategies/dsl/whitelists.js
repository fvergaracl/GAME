// Sprint 6: client-side mirror of the backend whitelists from
// app/engine/dsl_ast.py. These power the Blockly dropdowns and the
// client-side validator so the designer gets immediate feedback before
// the AST round-trips through the backend.
//
// IMPORTANT: keep in lockstep with app/engine/dsl_ast.py — see the
// note in the constant-block at the top of that file. Drift here means
// either the editor offers a path the backend rejects (bad UX) or the
// editor refuses a path the backend would accept (silent feature loss).

export const FIELD_PATHS = [
  'externalGameId',
  'externalTaskId',
  'externalUserId',
  'user.measurements_count',
  'task.measurements_count',
  'user.avg_time',
  'all.avg_time',
  'user.last_window_diff',
  'user.new_last_window_diff',
  // Sprint 6: rolling-window count for constantEffort-style strategies.
  'user.recent_measurements_count',
]

// Sprint 7: paths that read the parent built-in's result in DSL_EXTEND
// mode. The validator only accepts these inside post_rules — using
// them anywhere else would read uninitialised state because the
// parent hasn't run yet.
export const PARENT_FIELD_PATHS = ['parent.points', 'parent.case_name']

export const COMPARE_OPS = ['<', '<=', '==', '!=', '>=', '>']
export const ARITH_OPS = ['+', '-', '*', '/', 'min', 'max']

// Non-binary built-ins addressable via the func_call node.
export const FUNC_NAMES = ['int', 'clamp']
export const FUNC_ARITY = { int: 1, clamp: 3 }

// Sprint 7: per-section statement whitelisting. Mirrors
// ``STATEMENT_ALLOWED_CONTEXTS`` in app/engine/dsl_ast.py — the
// validator uses this map to reject set_data outside pre_rules,
// set_points outside post_rules, etc.
export const STATEMENT_ALLOWED_CONTEXTS = {
  assign_points: new Set(['rule', 'default']),
  set_callback_data: new Set(['rule', 'default', 'pre', 'post']),
  return: new Set(['rule', 'default', 'pre', 'post']),
  set_data: new Set(['pre']),
  veto: new Set(['pre']),
  set_points: new Set(['post']),
  set_case_name: new Set(['post']),
}

// Sprint 7: keys that are NOT valid inside parent_variables. Currently
// any key starting with ``variable_`` is accepted; the registry-level
// "does this variable exist?" check happens server-side at create/
// update time so a malformed editor state never poisons the DB.
export const PARENT_VARIABLE_KEY_PREFIX = 'variable_'

// Mirrors app/engine/dsl_ast.py _CASE_NAME_RE — printable ASCII, 1-200
// chars, no control bytes.
export const CASE_NAME_REGEX = /^[\x20-\x7E]{1,200}$/

// Mirrors app/engine/dsl_ast.py is_valid_data_path — data.<key> with
// alphanumeric/underscore key.
export const DATA_PATH_REGEX = /^data\.[A-Za-z0-9_]+$/

// Mirrors backend config limit so the editor can warn the designer
// before the backend rejects an oversized AST.
export const DSL_MAX_NODES = 1000
export const DSL_NODE_COUNT_WARN_THRESHOLD = 800
