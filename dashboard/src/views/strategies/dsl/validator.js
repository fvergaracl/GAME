// Sprint 6: client-side AST validator.
//
// This is a *thin mirror* of app/engine/dsl_validator.py — its job is
// purely UX: catch obvious mistakes (unknown field path, wrong arity,
// invalid case_name) before the backend round-trip so the designer
// gets feedback within the same paint frame. The backend remains the
// source of truth; anything we accept here that the backend would
// reject is just one POST + one toast away from the same error.
//
// Returns { ok: true } or { ok: false, errors: [{ nodeId, message }] }.

import {
  ARITH_OPS,
  CASE_NAME_REGEX,
  COMPARE_OPS,
  DATA_PATH_REGEX,
  DSL_MAX_NODES,
  FIELD_PATHS,
  FUNC_ARITY,
  FUNC_NAMES,
  PARENT_FIELD_PATHS,
  PARENT_VARIABLE_KEY_PREFIX,
  STATEMENT_ALLOWED_CONTEXTS,
} from './whitelists'

const CONDITION_TYPES = new Set(['and', 'or', 'not', 'compare', 'literal', 'field'])
const EXPRESSION_TYPES = new Set(['literal', 'field', 'arith', 'func_call'])
// Sprint 7: statement set expands with the 4 DSL_EXTEND statements.
// Per-section whitelisting (which statements are valid where) is
// enforced via STATEMENT_ALLOWED_CONTEXTS at validation time.
const STATEMENT_TYPES = new Set([
  'assign_points',
  'set_callback_data',
  'return',
  'set_data',
  'veto',
  'set_points',
  'set_case_name',
])

const PARENT_FIELD_PATH_SET = new Set(PARENT_FIELD_PATHS)

// ``code``/``params`` are optional and power the editor's localised,
// actionable messages (see friendlyValidationMessage in
// StrategyEditor.jsx). ``message`` stays the English machine string so
// it remains in lockstep with the backend validator and the existing
// validator.test.js regex assertions keep passing; the UI falls back to
// it when a code has no translation.
function fail(errors, nodeId, message, code = null, params = undefined) {
  errors.push({ nodeId: nodeId || null, message, code, params })
}

function isKnownFieldPath(path) {
  if (typeof path !== 'string' || path.length === 0) return false
  if (FIELD_PATHS.includes(path)) return true
  if (PARENT_FIELD_PATH_SET.has(path)) return true
  return DATA_PATH_REGEX.test(path)
}

function validateExpression(node, errors, nodeCount, context = 'rule') {
  nodeCount.value += 1
  if (!node || typeof node !== 'object' || Array.isArray(node)) {
    fail(errors, null, 'Expression must be an object.')
    return
  }
  if (!EXPRESSION_TYPES.has(node.type)) {
    fail(errors, node.id, `Unknown expression type: '${node.type}'.`)
    return
  }

  if (node.type === 'literal') {
    const v = node.value
    const isScalar =
      typeof v === 'string' ||
      typeof v === 'number' ||
      typeof v === 'boolean' ||
      v === null ||
      v === undefined
    if (!isScalar) {
      fail(errors, node.id, 'literal.value must be a JSON scalar.')
    }
    return
  }

  if (node.type === 'field') {
    if (!isKnownFieldPath(node.path)) {
      fail(
        errors,
        node.id,
        `field.path '${node.path}' is not in the allowed set.`,
        'FIELD_PATH_NOT_ALLOWED',
        { path: node.path },
      )
      return
    }
    // Sprint 7: parent.* only inside post_rules — mirrors backend.
    if (PARENT_FIELD_PATH_SET.has(node.path) && context !== 'post') {
      fail(errors, node.id, `field.path '${node.path}' is only available inside post_rules.`)
    }
    return
  }

  if (node.type === 'arith') {
    if (!ARITH_OPS.includes(node.op)) {
      fail(errors, node.id, `arith.op '${node.op}' is not allowed.`)
    }
    validateExpression(node.left, errors, nodeCount, context)
    validateExpression(node.right, errors, nodeCount, context)
    return
  }

  if (node.type === 'func_call') {
    if (!FUNC_NAMES.includes(node.name)) {
      fail(errors, node.id, `func_call.name '${node.name}' is not allowed.`)
      return
    }
    const expected = FUNC_ARITY[node.name]
    if (!Array.isArray(node.args) || node.args.length !== expected) {
      const actual = Array.isArray(node.args) ? node.args.length : 'non-list'
      fail(errors, node.id, `func_call '${node.name}' expects ${expected} args, got ${actual}.`)
      return
    }
    node.args.forEach((arg) => validateExpression(arg, errors, nodeCount, context))
  }
}

function validateCondition(node, errors, nodeCount, context = 'rule') {
  nodeCount.value += 1
  if (!node || typeof node !== 'object' || Array.isArray(node)) {
    fail(errors, null, 'Condition must be an object.')
    return
  }
  if (!CONDITION_TYPES.has(node.type)) {
    fail(errors, node.id, `Unknown condition type: '${node.type}'.`)
    return
  }

  if (node.type === 'and' || node.type === 'or') {
    if (!Array.isArray(node.args) || node.args.length === 0) {
      fail(errors, node.id, `${node.type}.args must be a non-empty array.`)
      return
    }
    node.args.forEach((arg) => validateCondition(arg, errors, nodeCount, context))
    return
  }
  if (node.type === 'not') {
    validateCondition(node.arg, errors, nodeCount, context)
    return
  }
  if (node.type === 'compare') {
    if (!COMPARE_OPS.includes(node.op)) {
      fail(errors, node.id, `compare.op '${node.op}' is not allowed.`)
    }
    validateExpression(node.left, errors, nodeCount, context)
    validateExpression(node.right, errors, nodeCount, context)
    return
  }
  // literal / field as bare condition — delegate to expression validation.
  validateExpression(node, errors, nodeCount, context)
}

function validateStatement(node, errors, nodeCount, context = 'rule') {
  nodeCount.value += 1
  if (!node || typeof node !== 'object' || Array.isArray(node)) {
    fail(errors, null, 'Statement must be an object.')
    return
  }
  if (!STATEMENT_TYPES.has(node.type)) {
    fail(errors, node.id, `Unknown statement type: '${node.type}'.`)
    return
  }
  // Sprint 7: per-section statement whitelisting BEFORE shape checks
  // so the error message points at the real designer problem.
  const allowed = STATEMENT_ALLOWED_CONTEXTS[node.type]
  if (!allowed || !allowed.has(context)) {
    fail(errors, node.id, `Statement '${node.type}' is not allowed inside '${context}' section.`)
    return
  }
  if (node.type === 'assign_points') {
    if (!CASE_NAME_REGEX.test(node.case_name || '')) {
      fail(errors, node.id, 'assign_points.case_name must be 1-200 printable ASCII chars.')
    }
    validateExpression(node.value, errors, nodeCount, context)
    return
  }
  if (node.type === 'set_callback_data') {
    if (typeof node.key !== 'string' || node.key.length === 0) {
      fail(errors, node.id, 'set_callback_data.key must be a non-empty string.')
    }
    validateExpression(node.value, errors, nodeCount, context)
    return
  }
  // Sprint 7: DSL_EXTEND statements ---------------------------------
  if (node.type === 'set_data') {
    if (typeof node.key !== 'string' || node.key.length === 0) {
      fail(errors, node.id, 'set_data.key must be a non-empty string.')
    } else if (!DATA_PATH_REGEX.test(`data.${node.key}`)) {
      fail(
        errors,
        node.id,
        "set_data.key must match [A-Za-z0-9_]+ (so it's readable via data.<key>).",
      )
    }
    validateExpression(node.value, errors, nodeCount, context)
    return
  }
  if (node.type === 'veto') {
    if (!CASE_NAME_REGEX.test(node.case_name || '')) {
      fail(errors, node.id, 'veto.case_name must be 1-200 printable ASCII chars.')
    }
    return
  }
  if (node.type === 'set_points') {
    validateExpression(node.value, errors, nodeCount, context)
    return
  }
  if (node.type === 'set_case_name') {
    validateExpression(node.value, errors, nodeCount, context)
    return
  }
  // return — no extra keys.
}

/**
 * Validate a JSON AST produced by ``workspaceToAst``.
 *
 * @param {object} ast - The AST to validate.
 * @returns {{ok: true, nodeCount: number, warning?: string} |
 *           {ok: false, errors: Array<{nodeId: string|null, message: string}>}}
 */
export function validateAst(ast) {
  const errors = []
  const nodeCount = { value: 0 }

  if (!ast || typeof ast !== 'object' || ast.type !== 'program') {
    return {
      ok: false,
      errors: [{ nodeId: null, message: "AST root must be a 'program' node." }],
    }
  }
  if (!Array.isArray(ast.rules)) {
    fail(errors, ast.id, 'program.rules must be an array.')
    return { ok: false, errors }
  }
  if (ast.rules.length === 0 && !ast.default) {
    fail(
      errors,
      ast.id,
      'program must have at least one rule or a default statement.',
      'PROGRAM_NO_RULES',
    )
  }

  const validateRuleArray = (section, sectionName, context) => {
    if (section == null) return
    if (!Array.isArray(section)) {
      fail(errors, ast.id, `program.${sectionName} must be an array.`)
      return
    }
    section.forEach((rule, i) => {
      nodeCount.value += 1
      if (!rule || rule.type !== 'rule') {
        fail(errors, rule?.id, `program.${sectionName}[${i}] must be a rule node.`)
        return
      }
      if (!rule.when) {
        fail(errors, rule.id, 'rule.when is required.', 'RULE_WHEN_REQUIRED')
      } else {
        validateCondition(rule.when, errors, nodeCount, context)
      }
      if (!Array.isArray(rule.then) || rule.then.length === 0) {
        fail(
          errors,
          rule.id,
          'rule.then must be a non-empty array of statements.',
          'RULE_THEN_EMPTY',
        )
      } else {
        rule.then.forEach((stmt) => validateStatement(stmt, errors, nodeCount, context))
      }
      // Sprint 12: optional else-if branches. Each is a {when, then}
      // object; ``then`` is validated exactly like the main branch so an
      // empty else-if body surfaces the same RULE_THEN_EMPTY error.
      if (rule.else_if != null) {
        if (!Array.isArray(rule.else_if)) {
          fail(errors, rule.id, 'rule.else_if must be an array.')
        } else {
          rule.else_if.forEach((branch, j) => {
            nodeCount.value += 1
            if (!branch || typeof branch !== 'object' || Array.isArray(branch)) {
              fail(errors, rule.id, `rule.else_if[${j}] must be an object.`)
              return
            }
            if (!branch.when) {
              fail(errors, rule.id, 'rule.else_if[].when is required.', 'RULE_WHEN_REQUIRED')
            } else {
              validateCondition(branch.when, errors, nodeCount, context)
            }
            if (!Array.isArray(branch.then) || branch.then.length === 0) {
              fail(
                errors,
                rule.id,
                'rule.else_if[].then must be a non-empty array of statements.',
                'RULE_THEN_EMPTY',
              )
            } else {
              branch.then.forEach((stmt) => validateStatement(stmt, errors, nodeCount, context))
            }
          })
        }
      }
      // Sprint 12: optional else branch — a non-empty statement list.
      if (rule.else != null) {
        if (!Array.isArray(rule.else) || rule.else.length === 0) {
          fail(
            errors,
            rule.id,
            'rule.else must be a non-empty array of statements.',
            'RULE_THEN_EMPTY',
          )
        } else {
          rule.else.forEach((stmt) => validateStatement(stmt, errors, nodeCount, context))
        }
      }
    })
  }

  validateRuleArray(ast.rules, 'rules', 'rule')
  // Sprint 7: pre_rules / post_rules are sibling sections to rules,
  // each with its own statement-context whitelist.
  validateRuleArray(ast.pre_rules, 'pre_rules', 'pre')
  validateRuleArray(ast.post_rules, 'post_rules', 'post')

  if (ast.default) {
    validateStatement(ast.default, errors, nodeCount, 'default')
  }

  // Sprint 7: parent_variables is an optional {var_name: scalar} map
  // applied to a fresh copy of the parent built-in before its
  // calculate_points runs. The registry-level "does this variable
  // exist?" check happens server-side at create/update time; here we
  // only enforce the AST shape so the editor catches malformed input
  // before the POST round-trip.
  if (ast.parent_variables !== undefined && ast.parent_variables !== null) {
    if (typeof ast.parent_variables !== 'object' || Array.isArray(ast.parent_variables)) {
      fail(errors, ast.id, 'program.parent_variables must be an object.')
    } else {
      Object.entries(ast.parent_variables).forEach(([key, value]) => {
        if (!key.startsWith(PARENT_VARIABLE_KEY_PREFIX)) {
          fail(
            errors,
            ast.id,
            `program.parent_variables key '${key}' must start with '${PARENT_VARIABLE_KEY_PREFIX}'.`,
          )
          return
        }
        const isScalar =
          typeof value === 'string' ||
          typeof value === 'number' ||
          typeof value === 'boolean' ||
          value === null
        if (!isScalar) {
          fail(errors, ast.id, `program.parent_variables['${key}'] must be a JSON scalar.`)
        }
      })
    }
  }

  if (errors.length > 0) {
    return { ok: false, errors }
  }
  if (nodeCount.value > DSL_MAX_NODES) {
    return {
      ok: false,
      errors: [
        {
          nodeId: null,
          message: `AST has ${nodeCount.value} nodes; the backend limit is ${DSL_MAX_NODES}.`,
        },
      ],
    }
  }
  return { ok: true, nodeCount: nodeCount.value }
}
