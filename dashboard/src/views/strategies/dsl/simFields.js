// Guided simulation inputs for the "Test strategy" panel.
//
// The /simulate endpoint accepts a flat ``mockState`` map of dotted-path
// → value overrides (see app/engine/dsl_execution_context.py). Designers
// used to type that JSON by hand; this module turns the analytics field
// whitelist into labelled inputs and powers the cumulative ("varios
// envíos") mode by deriving each run's mockState from a per-field step.
//
// IMPORTANT: ``path`` values mirror the analytics resolvers in
// app/engine/dsl_ast.py (FIELD_RESOLVERS) and FIELD_PATHS in
// ./whitelists.js. The static id paths (externalGameId/TaskId/UserId)
// and data.* paths are intentionally excluded - the former have their
// own inputs in the panel, the latter flow through the Event data box.

// ``kind`` drives the default per-submission step in cumulative mode:
// counts grow by 1 each submission, time fields stay fixed unless the
// designer overrides the step. Labels live in i18n under simulate.fields.
export const ACCUMULATION_FIELD_META = [
  { path: 'user.measurements_count', kind: 'count', default: 0, step: 1 },
  { path: 'task.measurements_count', kind: 'count', default: 0, step: 1 },
  { path: 'user.recent_measurements_count', kind: 'count', default: 0, step: 1 },
  { path: 'user.avg_time', kind: 'seconds', default: 0, step: 0 },
  { path: 'all.avg_time', kind: 'seconds', default: 0, step: 0 },
  { path: 'user.last_window_diff', kind: 'seconds', default: 0, step: 0 },
  { path: 'user.new_last_window_diff', kind: 'seconds', default: 0, step: 0 },
]

export const ACCUMULATION_FIELD_PATHS = ACCUMULATION_FIELD_META.map((m) => m.path)

const ACCUMULATION_FIELD_PATH_SET = new Set(ACCUMULATION_FIELD_PATHS)

// Walk the AST and collect every ``field`` node's path. The traversal is
// structure-agnostic on purpose: rules/when/then/args/left/right all nest
// differently (see ./generator.js), so we recurse into any object value
// or array element rather than hard-coding the shape.
export function collectUsedFieldPaths(ast) {
  const found = new Set()
  const visit = (node) => {
    if (Array.isArray(node)) {
      node.forEach(visit)
      return
    }
    if (!node || typeof node !== 'object') return
    if (node.type === 'field' && typeof node.path === 'string') {
      found.add(node.path)
    }
    for (const key of Object.keys(node)) {
      visit(node[key])
    }
  }
  visit(ast)
  return found
}

// The subset of ACCUMULATION_FIELD_META the strategy actually reads, in
// catalog order. Drives which labelled inputs the panel renders.
export function usedAccumulationFields(ast) {
  const used = collectUsedFieldPaths(ast)
  return ACCUMULATION_FIELD_META.filter((m) => used.has(m.path))
}

// Build the flat mockState override map for a single run. ``fieldValues``
// is ``{ [path]: { value, step } }``; only paths in ``usedPaths`` with a
// finite numeric value are emitted, so an unused field never shadows the
// real analytics call. ``runIndex`` (0-based) shifts each value by
// step*runIndex for the cumulative mode - runIndex 0 yields the base.
export function buildMockState(fieldValues, usedPaths, runIndex = 0) {
  const mock = {}
  for (const path of usedPaths) {
    if (!ACCUMULATION_FIELD_PATH_SET.has(path)) continue
    const entry = fieldValues[path]
    if (!entry) continue
    // Treat a cleared input ('' / null) as "not provided" so it doesn't
    // force a misleading explicit 0 (Number('') === 0).
    if (entry.value === '' || entry.value == null) continue
    const base = Number(entry.value)
    if (!Number.isFinite(base)) continue
    const step = Number(entry.step)
    const delta = Number.isFinite(step) ? step * runIndex : 0
    mock[path] = base + delta
  }
  return mock
}
