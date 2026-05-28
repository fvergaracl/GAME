// Sprint 6: AST generator — walks a Blockly workspace and emits JSON
// matching app/engine/dsl_ast.py's grammar exactly.
//
// We deliberately do NOT extend ``Blockly.Generator`` / use
// ``Blockly.JavaScript``. Those are designed for text-based code
// emission with scrubbing and indentation; we want plain JSON trees
// and explicit control over what becomes a rule vs a default.
//
// Each generator function is pure and testable without React or the
// DOM — a unit test can ``new Blockly.Workspace()``, populate it with
// ``workspace.newBlock('gd_rule')`` etc., and snapshot the output.
//
// Convention: every emitted node carries ``id = block.id`` so the
// backend execution trace points back at the exact Blockly block. This
// is what lets the simulate panel highlight the rule that fired.

const BLOCK_TO_AST = {
  gd_rule: blockToRule,
  gd_pre_rule: blockToRule,        // pre/post rules share the rule shape
  gd_post_rule: blockToRule,
  gd_compare: blockToCompare,
  gd_and: blockToAnd,
  gd_or: blockToOr,
  gd_not: blockToNot,
  gd_field: blockToField,
  gd_field_data: blockToFieldData,
  gd_field_parent: blockToFieldParent,
  gd_literal_number: blockToLiteralNumber,
  gd_literal_text: blockToLiteralText,
  gd_arith: blockToArith,
  gd_func_call: blockToFuncCall,
  gd_assign_points: blockToAssignPoints,
  gd_set_callback_data: blockToSetCallbackData,
  gd_set_data: blockToSetData,
  gd_veto: blockToVeto,
  gd_set_points: blockToSetPoints,
  gd_set_case_name: blockToSetCaseName,
}

/**
 * Convert a Blockly workspace to a JSON AST.
 *
 * Top-level routing:
 * * ``gd_rule`` blocks → ``program.rules[]`` (DSL_FULL behaviour).
 * * ``gd_pre_rule`` blocks → ``program.pre_rules[]`` (Sprint 7).
 * * ``gd_post_rule`` blocks → ``program.post_rules[]`` (Sprint 7).
 * * A floating ``gd_assign_points`` (no previous connection) →
 *   ``program.default``.
 * * ``gd_parent_variable_override`` blocks → ``program.parent_variables``
 *   map (Sprint 7).
 *
 * @param {Blockly.Workspace} workspace
 * @returns {object} AST root (always type 'program')
 */
export function workspaceToAst(workspace) {
  const topBlocks = workspace.getTopBlocks(true)
  const rules = []
  const preRules = []
  const postRules = []
  const parentVariables = {}
  let defaultStmt = null

  for (const block of topBlocks) {
    if (block.type === 'gd_rule') {
      rules.push(blockToRule(block))
    } else if (block.type === 'gd_pre_rule') {
      preRules.push(blockToRule(block))
    } else if (block.type === 'gd_post_rule') {
      postRules.push(blockToRule(block))
    } else if (block.type === 'gd_parent_variable_override') {
      const name = block.getFieldValue('VARIABLE')
      const raw = block.getFieldValue('VALUE')
      parentVariables[name] = _coerceOverrideValue(raw)
    } else if (
      block.type === 'gd_assign_points' &&
      !block.getPreviousBlock()
    ) {
      // A floating assign_points outside any rule is the default branch.
      // Limit to one: extras silently win-last (the order Blockly returns).
      defaultStmt = blockToAssignPoints(block)
    }
    // Other top-level blocks are ignored — they're orphans waiting to be
    // wired up. We don't crash on them so the designer can keep drafting.
  }

  const ast = { type: 'program', id: 'program', rules }
  if (preRules.length > 0) ast.pre_rules = preRules
  if (postRules.length > 0) ast.post_rules = postRules
  if (Object.keys(parentVariables).length > 0) {
    ast.parent_variables = parentVariables
  }
  if (defaultStmt) ast.default = defaultStmt
  return ast
}

// gd_parent_variable_override uses two FieldTextInputs (variable name +
// value) for simplicity — the editor pre-fills them from the parent
// schema. We coerce the value string into a JSON scalar: numeric
// strings parse to numbers, "true"/"false"/"null" map to those
// literals, anything else stays a string. The validator and backend
// will reject non-scalars like arrays/objects.
// Accepts integers, decimals (incl. leading-dot / trailing-dot) and
// scientific notation, with an optional sign — e.g. 42, -1.5, .5, 1.,
// 1e3, -2.5E-4. Deliberately excludes hex/octal/Infinity/NaN so a stray
// "0x10" or "Infinity" stays a string the backend will reject loudly
// rather than silently coercing to something unexpected.
const _NUMERIC_RE = /^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$/

function _coerceOverrideValue(raw) {
  if (raw === undefined || raw === null) return null
  const trimmed = String(raw).trim()
  if (trimmed === 'true') return true
  if (trimmed === 'false') return false
  if (trimmed === 'null') return null
  if (trimmed === '') return ''
  // Prefer numeric coercion if the string parses cleanly as a number.
  // The regex guarantees Number() yields a finite value (no hex/Infinity).
  if (_NUMERIC_RE.test(trimmed)) return Number(trimmed)
  return trimmed
}

// ---------------------------------------------------------------------------
// Rule + statements
// ---------------------------------------------------------------------------

function blockToRule(block) {
  const whenBlock = block.getInputTargetBlock('WHEN')
  const thenBlock = block.getInputTargetBlock('THEN')
  const node = {
    type: 'rule',
    id: block.id,
    when: whenBlock ? blockToCondition(whenBlock) : null,
    then: collectStatements(thenBlock),
  }

  // Sprint 12: optional else-if / else branches added via the rule
  // mutator. Extra branches use IF{i}/DO{i} (i >= 1) value+statement
  // input pairs; the else clause is a single ELSE statement input. We
  // probe by input presence (block.getInput) rather than the private
  // elseifCount_ counter so the AST stays correct even if a branch was
  // re-shaped without updating the counter. The keys are omitted when
  // empty so rules without branches produce the exact pre-Sprint-12 AST.
  const elseIf = []
  for (let i = 1; block.getInput(`IF${i}`); i++) {
    const branchWhen = block.getInputTargetBlock(`IF${i}`)
    elseIf.push({
      when: branchWhen ? blockToCondition(branchWhen) : null,
      then: collectStatements(block.getInputTargetBlock(`DO${i}`)),
    })
  }
  if (elseIf.length > 0) node.else_if = elseIf
  if (block.getInput('ELSE')) {
    node.else = collectStatements(block.getInputTargetBlock('ELSE'))
  }
  return node
}

function collectStatements(firstBlock) {
  const out = []
  let cursor = firstBlock
  while (cursor) {
    out.push(blockToStatement(cursor))
    cursor = cursor.getNextBlock()
  }
  return out
}

function blockToStatement(block) {
  if (block.type === 'gd_assign_points') return blockToAssignPoints(block)
  if (block.type === 'gd_set_callback_data') return blockToSetCallbackData(block)
  // Sprint 7 statements.
  if (block.type === 'gd_set_data') return blockToSetData(block)
  if (block.type === 'gd_veto') return blockToVeto(block)
  if (block.type === 'gd_set_points') return blockToSetPoints(block)
  if (block.type === 'gd_set_case_name') return blockToSetCaseName(block)
  return { type: 'unknown', id: block.id, blockType: block.type }
}

function blockToAssignPoints(block) {
  const valueBlock = block.getInputTargetBlock('VALUE')
  return {
    type: 'assign_points',
    id: block.id,
    value: valueBlock
      ? blockToExpression(valueBlock)
      : { type: 'literal', id: `${block.id}_v_missing`, value: 0 },
    case_name: block.getFieldValue('CASE_NAME') || 'default',
  }
}

function blockToSetCallbackData(block) {
  const valueBlock = block.getInputTargetBlock('VALUE')
  return {
    type: 'set_callback_data',
    id: block.id,
    key: block.getFieldValue('KEY') || '',
    value: valueBlock
      ? blockToExpression(valueBlock)
      : { type: 'literal', id: `${block.id}_v_missing`, value: null },
  }
}

// Sprint 7 statement converters --------------------------------------------

function blockToSetData(block) {
  const valueBlock = block.getInputTargetBlock('VALUE')
  return {
    type: 'set_data',
    id: block.id,
    key: block.getFieldValue('KEY') || '',
    value: valueBlock
      ? blockToExpression(valueBlock)
      : { type: 'literal', id: `${block.id}_v_missing`, value: null },
  }
}

function blockToVeto(block) {
  return {
    type: 'veto',
    id: block.id,
    case_name: block.getFieldValue('CASE_NAME') || 'Vetoed',
  }
}

function blockToSetPoints(block) {
  const valueBlock = block.getInputTargetBlock('VALUE')
  return {
    type: 'set_points',
    id: block.id,
    value: valueBlock
      ? blockToExpression(valueBlock)
      : { type: 'literal', id: `${block.id}_v_missing`, value: 0 },
  }
}

function blockToSetCaseName(block) {
  const valueBlock = block.getInputTargetBlock('VALUE')
  return {
    type: 'set_case_name',
    id: block.id,
    value: valueBlock
      ? blockToExpression(valueBlock)
      : { type: 'literal', id: `${block.id}_v_missing`, value: '' },
  }
}

// ---------------------------------------------------------------------------
// Conditions
// ---------------------------------------------------------------------------

function blockToCondition(block) {
  if (block.type === 'gd_compare') return blockToCompare(block)
  if (block.type === 'gd_and') return blockToAnd(block)
  if (block.type === 'gd_or') return blockToOr(block)
  if (block.type === 'gd_not') return blockToNot(block)
  // Bare expression as condition — passes through to expression conversion.
  return blockToExpression(block)
}

function blockToCompare(block) {
  return {
    type: 'compare',
    id: block.id,
    op: block.getFieldValue('OP'),
    left: _exprOrMissing(block, 'LEFT'),
    right: _exprOrMissing(block, 'RIGHT'),
  }
}

function blockToAnd(block) {
  return {
    type: 'and',
    id: block.id,
    args: _twoConditions(block, 'A', 'B'),
  }
}

function blockToOr(block) {
  return {
    type: 'or',
    id: block.id,
    args: _twoConditions(block, 'A', 'B'),
  }
}

function blockToNot(block) {
  const inner = block.getInputTargetBlock('ARG')
  return {
    type: 'not',
    id: block.id,
    arg: inner ? blockToCondition(inner) : _missingLiteral(`${block.id}_arg`),
  }
}

// ---------------------------------------------------------------------------
// Expressions
// ---------------------------------------------------------------------------

function blockToExpression(block) {
  const converter = BLOCK_TO_AST[block.type]
  if (converter) return converter(block)
  return { type: 'unknown', id: block.id, blockType: block.type }
}

function blockToField(block) {
  return {
    type: 'field',
    id: block.id,
    path: block.getFieldValue('PATH'),
  }
}

function blockToFieldData(block) {
  const key = block.getFieldValue('KEY') || ''
  return {
    type: 'field',
    id: block.id,
    path: `data.${key}`,
  }
}

// Sprint 7: reads parent.points / parent.case_name. The dropdown stores
// the full path string as its value so emission is one-line.
function blockToFieldParent(block) {
  return {
    type: 'field',
    id: block.id,
    path: block.getFieldValue('PATH'),
  }
}

function blockToLiteralNumber(block) {
  return {
    type: 'literal',
    id: block.id,
    value: Number(block.getFieldValue('VALUE')),
  }
}

function blockToLiteralText(block) {
  return {
    type: 'literal',
    id: block.id,
    value: block.getFieldValue('VALUE') || '',
  }
}

function blockToArith(block) {
  return {
    type: 'arith',
    id: block.id,
    op: block.getFieldValue('OP'),
    left: _exprOrMissing(block, 'LEFT'),
    right: _exprOrMissing(block, 'RIGHT'),
  }
}

function blockToFuncCall(block) {
  const name = block.getFieldValue('NAME')
  const args = []
  if (name === 'int') {
    args.push(_exprOrMissing(block, 'VALUE'))
  } else if (name === 'clamp') {
    args.push(_exprOrMissing(block, 'VALUE'))
    args.push(_exprOrMissing(block, 'LO'))
    args.push(_exprOrMissing(block, 'HI'))
  }
  return { type: 'func_call', id: block.id, name, args }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function _exprOrMissing(parentBlock, inputName) {
  const target = parentBlock.getInputTargetBlock(inputName)
  return target
    ? blockToExpression(target)
    : _missingLiteral(`${parentBlock.id}_${inputName.toLowerCase()}_missing`)
}

function _twoConditions(parentBlock, inputA, inputB) {
  const a = parentBlock.getInputTargetBlock(inputA)
  const b = parentBlock.getInputTargetBlock(inputB)
  return [
    a ? blockToCondition(a) : _missingLiteral(`${parentBlock.id}_${inputA}_missing`),
    b ? blockToCondition(b) : _missingLiteral(`${parentBlock.id}_${inputB}_missing`),
  ]
}

function _missingLiteral(id) {
  // We emit a literal-false sentinel for any unwired input so the AST is
  // still structurally complete. The validator will catch the empty
  // workspace as a separate error ("rule.then must be non-empty" etc.)
  // — designers should not see this surface in normal use.
  return { type: 'literal', id, value: false }
}
