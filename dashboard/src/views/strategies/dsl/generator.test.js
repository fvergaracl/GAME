// Sprint 6: generator tests — snapshot-style assertions that pin the
// workspace→AST mapping. Each test builds a known workspace using the
// headless Blockly API (no DOM, no react), runs ``workspaceToAst``,
// and checks the JSON shape matches what the backend interpreter
// expects (and what the parity test for default.py asserts upstream).

import { beforeAll, describe, expect, it } from 'vitest'
import * as Blockly from 'blockly/core'

import { registerDslBlocks } from '../blocks'
import { workspaceToAst } from './generator'
import { validateAst } from './validator'

beforeAll(() => {
  registerDslBlocks()
})

/**
 * Helper that initialises a brand-new headless workspace per test so we
 * don't carry block state across the suite.
 */
function makeWorkspace() {
  return new Blockly.Workspace()
}

/**
 * Stable-id helper: ``workspace.newBlock(type, id)`` accepts an explicit
 * id and registers the block under it. We can NOT overwrite ``block.id``
 * after construction because Blockly indexes blocks by id internally and
 * subsequent ``connection.connect`` calls would emit BlockMove events
 * that look up the block by the wrong id and crash.
 */
function newBlock(ws, type, id) {
  return ws.newBlock(type, id)
}

/**
 * Connect ``childOutput`` of ``child`` to ``inputName`` of ``parent``.
 * Wraps the Blockly connection API which throws on type mismatches.
 */
function connectChildToInput(parent, inputName, child) {
  const input = parent.getInput(inputName)
  expect(input).toBeTruthy()
  input.connection.connect(child.outputConnection)
}

/**
 * Snap ``child`` onto ``parent``'s ``inputName`` statement stack.
 */
function connectChildStatement(parent, inputName, child) {
  const input = parent.getInput(inputName)
  expect(input).toBeTruthy()
  input.connection.connect(child.previousConnection)
}

describe('workspaceToAst — empty workspace', () => {
  it('produces a program with no rules and no default', () => {
    const ws = makeWorkspace()

    const ast = workspaceToAst(ws)

    expect(ast).toEqual({ type: 'program', id: 'program', rules: [] })
  })
})

describe('workspaceToAst — basic engagement rule', () => {
  it('reproduces the BasicEngagement scenario from default.py', () => {
    // Build the workspace equivalent of:
    //   when task.measurements_count < 2
    //   then assign_points 1, "BasicEngagement"
    const ws = makeWorkspace()

    const rule = newBlock(ws, 'gd_rule', 'r1')

    const compare = newBlock(ws, 'gd_compare', 'c1')
    compare.setFieldValue('<', 'OP')

    const field = newBlock(ws, 'gd_field', 'f1')
    field.setFieldValue('task.measurements_count', 'PATH')

    const threshold = newBlock(ws, 'gd_literal_number', 'l1')
    threshold.setFieldValue('2', 'VALUE')

    connectChildToInput(compare, 'LEFT', field)
    connectChildToInput(compare, 'RIGHT', threshold)
    connectChildToInput(rule, 'WHEN', compare)

    const assign = newBlock(ws, 'gd_assign_points', 'a1')
    assign.setFieldValue('BasicEngagement', 'CASE_NAME')

    const pointsValue = newBlock(ws, 'gd_literal_number', 'lv1')
    pointsValue.setFieldValue('1', 'VALUE')
    connectChildToInput(assign, 'VALUE', pointsValue)

    connectChildStatement(rule, 'THEN', assign)

    const ast = workspaceToAst(ws)

    expect(ast).toEqual({
      type: 'program',
      id: 'program',
      rules: [
        {
          type: 'rule',
          id: 'r1',
          when: {
            type: 'compare',
            id: 'c1',
            op: '<',
            left: { type: 'field', id: 'f1', path: 'task.measurements_count' },
            right: { type: 'literal', id: 'l1', value: 2 },
          },
          then: [
            {
              type: 'assign_points',
              id: 'a1',
              value: { type: 'literal', id: 'lv1', value: 1 },
              case_name: 'BasicEngagement',
            },
          ],
        },
      ],
    })

    // Sanity: the generator output must pass the client-side validator
    // — anything the editor produces should round-trip cleanly.
    expect(validateAst(ast).ok).toBe(true)
  })
})

describe('workspaceToAst — default branch from a top-level assign_points', () => {
  it('treats an unparented assign_points as program.default', () => {
    const ws = makeWorkspace()

    const fallback = newBlock(ws, 'gd_assign_points', 'd1')
    fallback.setFieldValue('default', 'CASE_NAME')

    const lit = newBlock(ws, 'gd_literal_number', 'ld1')
    lit.setFieldValue('1', 'VALUE')
    connectChildToInput(fallback, 'VALUE', lit)

    const ast = workspaceToAst(ws)

    expect(ast).toEqual({
      type: 'program',
      id: 'program',
      rules: [],
      default: {
        type: 'assign_points',
        id: 'd1',
        value: { type: 'literal', id: 'ld1', value: 1 },
        case_name: 'default',
      },
    })
  })
})

describe('workspaceToAst — func_call with int and clamp', () => {
  it('emits the expected nested func_call structure for clamp(int(x), 1, 100)', () => {
    const ws = makeWorkspace()

    const rule = newBlock(ws, 'gd_rule', 'r1')
    const whenLit = newBlock(ws, 'gd_literal_number', 'wl')
    whenLit.setFieldValue('1', 'VALUE')
    // Bare expression as condition — passes through.
    connectChildToInput(rule, 'WHEN', whenLit)

    const assign = newBlock(ws, 'gd_assign_points', 'a1')
    assign.setFieldValue('Reward', 'CASE_NAME')

    const clamp = newBlock(ws, 'gd_func_call', 'fc_clamp')
    clamp.setFieldValue('clamp', 'NAME')
    // ``setFieldValue`` triggers the dropdown's onchange-via-setTimeout
    // path in production; in a sync test we force the rebuild ourselves
    // so the VALUE/LO/HI inputs exist before we try to connect them.
    clamp._rebuildArgs('clamp')

    const intCall = newBlock(ws, 'gd_func_call', 'fc_int')
    intCall.setFieldValue('int', 'NAME')
    intCall._rebuildArgs('int')

    const lo = newBlock(ws, 'gd_literal_number', 'l_lo')
    lo.setFieldValue('1', 'VALUE')
    const hi = newBlock(ws, 'gd_literal_number', 'l_hi')
    hi.setFieldValue('100', 'VALUE')
    const x = newBlock(ws, 'gd_literal_number', 'l_x')
    x.setFieldValue('42', 'VALUE')

    connectChildToInput(intCall, 'VALUE', x)
    connectChildToInput(clamp, 'VALUE', intCall)
    connectChildToInput(clamp, 'LO', lo)
    connectChildToInput(clamp, 'HI', hi)
    connectChildToInput(assign, 'VALUE', clamp)
    connectChildStatement(rule, 'THEN', assign)

    const ast = workspaceToAst(ws)

    expect(ast.rules[0].then[0].value).toEqual({
      type: 'func_call',
      id: 'fc_clamp',
      name: 'clamp',
      args: [
        {
          type: 'func_call',
          id: 'fc_int',
          name: 'int',
          args: [{ type: 'literal', id: 'l_x', value: 42 }],
        },
        { type: 'literal', id: 'l_lo', value: 1 },
        { type: 'literal', id: 'l_hi', value: 100 },
      ],
    })

    expect(validateAst(ast).ok).toBe(true)
  })
})

// =========================================================================
// Sprint 7 — DSL_EXTEND generator tests.
//
// Verify the top-level routing of gd_pre_rule / gd_post_rule into
// program.pre_rules / post_rules, the parent_variables map emission,
// and that the resulting AST passes the client-side validator.
// =========================================================================

describe('workspaceToAst — Sprint 7 pre/post + parent_variables', () => {
  it('emits pre_rules from top-level gd_pre_rule blocks', () => {
    const ws = makeWorkspace()
    const preRule = newBlock(ws, 'gd_pre_rule', 'pr1')

    const cond = newBlock(ws, 'gd_literal_number', 'cn')
    cond.setFieldValue('1', 'VALUE')
    connectChildToInput(preRule, 'WHEN', cond)

    const setData = newBlock(ws, 'gd_set_data', 'sd1')
    setData.setFieldValue('first_time', 'KEY')
    const lit = newBlock(ws, 'gd_literal_number', 'lv')
    lit.setFieldValue('1', 'VALUE')
    connectChildToInput(setData, 'VALUE', lit)

    connectChildStatement(preRule, 'THEN', setData)

    const ast = workspaceToAst(ws)

    expect(ast.pre_rules).toBeDefined()
    expect(ast.pre_rules).toHaveLength(1)
    expect(ast.pre_rules[0].id).toBe('pr1')
    expect(ast.pre_rules[0].then[0]).toMatchObject({
      type: 'set_data',
      key: 'first_time',
    })
    expect(ast.rules).toEqual([])
  })

  it('emits post_rules with set_points reading parent.points', () => {
    const ws = makeWorkspace()
    const postRule = newBlock(ws, 'gd_post_rule', 'po1')

    const cond = newBlock(ws, 'gd_literal_number', 'cn')
    cond.setFieldValue('1', 'VALUE')
    connectChildToInput(postRule, 'WHEN', cond)

    const setPoints = newBlock(ws, 'gd_set_points', 'sp1')
    const parentField = newBlock(ws, 'gd_field_parent', 'fp')
    parentField.setFieldValue('parent.points', 'PATH')
    connectChildToInput(setPoints, 'VALUE', parentField)

    connectChildStatement(postRule, 'THEN', setPoints)

    const ast = workspaceToAst(ws)
    // Add a default so the validator accepts the program (rules=[]).
    ast.default = {
      type: 'assign_points',
      id: 'd',
      value: { type: 'literal', id: 'ld', value: 0 },
      case_name: 'baseline',
    }

    expect(ast.post_rules).toBeDefined()
    expect(ast.post_rules[0].then[0]).toMatchObject({
      type: 'set_points',
      value: { type: 'field', path: 'parent.points' },
    })

    // The whole thing must pass the client validator (which now knows
    // that parent.points is OK inside post_rules).
    expect(validateAst(ast).ok).toBe(true)
  })

  it('emits parent_variables map from top-level override blocks with type coercion', () => {
    const ws = makeWorkspace()

    const ovInt = newBlock(ws, 'gd_parent_variable_override', 'ov1')
    ovInt.setFieldValue('variable_basic_points', 'VARIABLE')
    ovInt.setFieldValue('42', 'VALUE')

    const ovFloat = newBlock(ws, 'gd_parent_variable_override', 'ov2')
    ovFloat.setFieldValue('variable_factor', 'VARIABLE')
    ovFloat.setFieldValue('1.5', 'VALUE')

    const ovBool = newBlock(ws, 'gd_parent_variable_override', 'ov3')
    ovBool.setFieldValue('variable_debug', 'VARIABLE')
    ovBool.setFieldValue('true', 'VALUE')

    const ovStr = newBlock(ws, 'gd_parent_variable_override', 'ov4')
    ovStr.setFieldValue('variable_label', 'VARIABLE')
    ovStr.setFieldValue('custom-label', 'VALUE')

    // Need at least a default so validateAst accepts the program.
    const fallback = newBlock(ws, 'gd_assign_points', 'd')
    fallback.setFieldValue('baseline', 'CASE_NAME')
    const lit = newBlock(ws, 'gd_literal_number', 'ld')
    lit.setFieldValue('1', 'VALUE')
    connectChildToInput(fallback, 'VALUE', lit)

    const ast = workspaceToAst(ws)

    expect(ast.parent_variables).toEqual({
      variable_basic_points: 42,
      variable_factor: 1.5,
      variable_debug: true,
      variable_label: 'custom-label',
    })

    expect(validateAst(ast).ok).toBe(true)
  })

  it('omits pre_rules / post_rules / parent_variables when nothing wired', () => {
    // Sanity: empty DSL_EXTEND workspace shouldn't produce empty
    // sections (that would force the editor into DSL_EXTEND on the
    // backend even for DSL_FULL strategies).
    const ws = makeWorkspace()
    const ast = workspaceToAst(ws)
    expect(ast.pre_rules).toBeUndefined()
    expect(ast.post_rules).toBeUndefined()
    expect(ast.parent_variables).toBeUndefined()
  })
})

describe('workspaceToAst — invalid output still validates structurally', () => {
  it('a rule whose then is empty produces an empty array (caught by validator)', () => {
    const ws = makeWorkspace()
    const rule = newBlock(ws, 'gd_rule', 'r1')
    const lit = newBlock(ws, 'gd_literal_number', 'wl')
    lit.setFieldValue('1', 'VALUE')
    connectChildToInput(rule, 'WHEN', lit)

    const ast = workspaceToAst(ws)

    expect(ast.rules[0].then).toEqual([])
    const result = validateAst(ast)
    expect(result.ok).toBe(false)
    // The validator must flag the empty `then` — that's the contract.
    expect(result.errors.some((e) => /non-empty array of statements/.test(e.message))).toBe(true)
  })
})

describe('workspaceToAst — else-if / else branches (mutator)', () => {
  // Small helper: an assign_points statement with a literal number value.
  function assignBlock(ws, id, value, caseName) {
    const assign = newBlock(ws, 'gd_assign_points', id)
    assign.setFieldValue(caseName, 'CASE_NAME')
    const lit = newBlock(ws, 'gd_literal_number', `${id}_v`)
    lit.setFieldValue(String(value), 'VALUE')
    connectChildToInput(assign, 'VALUE', lit)
    return assign
  }

  it('a rule with no branches omits else_if / else entirely', () => {
    const ws = makeWorkspace()
    const rule = newBlock(ws, 'gd_rule', 'r1')
    const lit = newBlock(ws, 'gd_literal_number', 'wl')
    lit.setFieldValue('1', 'VALUE')
    connectChildToInput(rule, 'WHEN', lit)
    connectChildStatement(rule, 'THEN', assignBlock(ws, 'a1', 1, 'A'))

    const ast = workspaceToAst(ws)

    expect(ast.rules[0]).not.toHaveProperty('else_if')
    expect(ast.rules[0]).not.toHaveProperty('else')
  })

  it('emits else_if[] and else from the mutator-expanded inputs', () => {
    const ws = makeWorkspace()
    const rule = newBlock(ws, 'gd_rule', 'r1')

    // Expand the shape: one else-if branch + an else branch. This is the
    // same JSON shape Blockly's serializer round-trips via loadExtraState.
    rule.loadExtraState({ elseIfCount: 1, hasElse: true })

    // Base branch: when true → assign 1 / "A".
    const whenLit = newBlock(ws, 'gd_literal_number', 'wl')
    whenLit.setFieldValue('1', 'VALUE')
    connectChildToInput(rule, 'WHEN', whenLit)
    connectChildStatement(rule, 'THEN', assignBlock(ws, 'a1', 1, 'A'))

    // else-if branch: when true → assign 2 / "B".
    const elifLit = newBlock(ws, 'gd_literal_number', 'el')
    elifLit.setFieldValue('1', 'VALUE')
    connectChildToInput(rule, 'IF1', elifLit)
    connectChildStatement(rule, 'DO1', assignBlock(ws, 'a2', 2, 'B'))

    // else branch: assign 3 / "C".
    connectChildStatement(rule, 'ELSE', assignBlock(ws, 'a3', 3, 'C'))

    const ast = workspaceToAst(ws)
    const r = ast.rules[0]

    expect(r.then).toEqual([
      {
        type: 'assign_points',
        id: 'a1',
        value: { type: 'literal', id: 'a1_v', value: 1 },
        case_name: 'A',
      },
    ])
    expect(r.else_if).toEqual([
      {
        when: { type: 'literal', id: 'el', value: 1 },
        then: [
          {
            type: 'assign_points',
            id: 'a2',
            value: { type: 'literal', id: 'a2_v', value: 2 },
            case_name: 'B',
          },
        ],
      },
    ])
    expect(r.else).toEqual([
      {
        type: 'assign_points',
        id: 'a3',
        value: { type: 'literal', id: 'a3_v', value: 3 },
        case_name: 'C',
      },
    ])

    // The full thing must pass the client validator.
    expect(validateAst(ast).ok).toBe(true)
  })
})
