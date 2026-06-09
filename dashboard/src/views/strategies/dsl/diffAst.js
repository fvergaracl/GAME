// AST diffing for the version history modal.
//
// Compares two DSL ``program`` ASTs (the JSON shape emitted by
// ``workspaceToAst`` in generator.js) and returns a structured diff
// the UI can render rule-by-rule with added/removed/modified badges.
//
// Strategy: match rules by their stable ``id`` (= Blockly block id).
// When a designer edits a workspace the ids of preserved blocks are
// kept across PUT/version-fork roundtrips, so id-based matching
// reliably distinguishes "same rule, body changed" from "rule replaced".
// Falls back to positional matching only for nodes without ids - in
// practice the generator always emits ids, but the fallback keeps the
// diff useful for hand-authored ASTs and imports.
//
// The output is JSON-only; rendering colours/icons happens in the
// modal so this stays unit-testable without DOM.

const KIND_ADDED = 'added'
const KIND_REMOVED = 'removed'
const KIND_MODIFIED = 'modified'
const KIND_UNCHANGED = 'unchanged'

// Stable structural equality - JSON.stringify is "good enough" given
// the AST is plain JSON and the ordering convention is fixed by the
// generator. We sort object keys to be tolerant of payloads that
// round-tripped through different serialisers (the backend stores
// astJson as JSONB; PostgreSQL doesn't preserve key order).
function _canonical(value) {
  if (value === null || typeof value !== 'object') return JSON.stringify(value)
  if (Array.isArray(value)) {
    return `[${value.map(_canonical).join(',')}]`
  }
  const keys = Object.keys(value).sort()
  return `{${keys.map((k) => `${JSON.stringify(k)}:${_canonical(value[k])}`).join(',')}}`
}

function _deepEqual(a, b) {
  return _canonical(a) === _canonical(b)
}

/**
 * Diff two arrays of rule-like nodes. Each rule carries an ``id``;
 * matching is done by id, so re-ordering doesn't show as
 * added/removed.
 *
 * Returns an ordered list following B's layout first (so the UI reads
 * top-to-bottom in the order the latest version presents), with
 * removed-only items appended at the end.
 */
function _diffRuleList(listA, listB) {
  const a = Array.isArray(listA) ? listA : []
  const b = Array.isArray(listB) ? listB : []
  const indexA = new Map(a.map((rule, i) => [rule?.id ?? `__pos_${i}`, rule]))
  const seenIds = new Set()
  const out = []

  b.forEach((ruleB, i) => {
    const id = ruleB?.id ?? `__pos_${i}`
    const ruleA = indexA.get(id)
    if (ruleA == null) {
      out.push({ kind: KIND_ADDED, id, a: null, b: ruleB })
    } else if (_deepEqual(ruleA, ruleB)) {
      out.push({ kind: KIND_UNCHANGED, id, a: ruleA, b: ruleB })
    } else {
      out.push({ kind: KIND_MODIFIED, id, a: ruleA, b: ruleB })
    }
    seenIds.add(id)
  })

  a.forEach((ruleA, i) => {
    const id = ruleA?.id ?? `__pos_${i}`
    if (seenIds.has(id)) return
    out.push({ kind: KIND_REMOVED, id, a: ruleA, b: null })
  })

  return out
}

function _diffNode(a, b) {
  const present = a != null || b != null
  if (!present) return null
  if (a == null) return { kind: KIND_ADDED, a: null, b }
  if (b == null) return { kind: KIND_REMOVED, a, b: null }
  if (_deepEqual(a, b)) return { kind: KIND_UNCHANGED, a, b }
  return { kind: KIND_MODIFIED, a, b }
}

function _diffParentVariables(mapA, mapB) {
  const a = mapA && typeof mapA === 'object' ? mapA : {}
  const b = mapB && typeof mapB === 'object' ? mapB : {}
  const keys = new Set([...Object.keys(a), ...Object.keys(b)])
  const sorted = Array.from(keys).sort()
  return sorted.map((key) => {
    const hasA = Object.prototype.hasOwnProperty.call(a, key)
    const hasB = Object.prototype.hasOwnProperty.call(b, key)
    if (hasA && !hasB) return { key, kind: KIND_REMOVED, a: a[key], b: undefined }
    if (!hasA && hasB) return { key, kind: KIND_ADDED, a: undefined, b: b[key] }
    if (_deepEqual(a[key], b[key])) {
      return { key, kind: KIND_UNCHANGED, a: a[key], b: b[key] }
    }
    return { key, kind: KIND_MODIFIED, a: a[key], b: b[key] }
  })
}

/**
 * Compare two ``program`` ASTs and emit a per-section diff.
 *
 * Inputs may be ``null`` or ``undefined`` (e.g. a strategy was created
 * without an AST yet). They're normalised to empty programs.
 *
 * @param {object|null} astA
 * @param {object|null} astB
 * @returns {{
 *   rules: Array<{kind: string, id: string, a: object|null, b: object|null}>,
 *   pre_rules: Array<...>,
 *   post_rules: Array<...>,
 *   default: {kind: string, a: any, b: any}|null,
 *   parent_variables: Array<{key: string, kind: string, a: any, b: any}>,
 *   summary: {added: number, removed: number, modified: number, unchanged: number},
 * }}
 */
export function diffPrograms(astA, astB) {
  const a = astA || {}
  const b = astB || {}
  const rules = _diffRuleList(a.rules, b.rules)
  const pre = _diffRuleList(a.pre_rules, b.pre_rules)
  const post = _diffRuleList(a.post_rules, b.post_rules)
  const def = _diffNode(a.default, b.default)
  const parentVars = _diffParentVariables(a.parent_variables, b.parent_variables)

  const summary = {
    [KIND_ADDED]: 0,
    [KIND_REMOVED]: 0,
    [KIND_MODIFIED]: 0,
    [KIND_UNCHANGED]: 0,
  }
  const collectKind = (entry) => {
    if (!entry) return
    summary[entry.kind] = (summary[entry.kind] || 0) + 1
  }
  rules.forEach(collectKind)
  pre.forEach(collectKind)
  post.forEach(collectKind)
  collectKind(def)
  parentVars.forEach(collectKind)

  return {
    rules,
    pre_rules: pre,
    post_rules: post,
    default: def,
    parent_variables: parentVars,
    summary,
  }
}

export const DIFF_KINDS = {
  ADDED: KIND_ADDED,
  REMOVED: KIND_REMOVED,
  MODIFIED: KIND_MODIFIED,
  UNCHANGED: KIND_UNCHANGED,
}
