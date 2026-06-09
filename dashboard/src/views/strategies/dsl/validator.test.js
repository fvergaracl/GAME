// Client-side AST validator tests.
//
// Targets the rejection paths the validator is responsible for - the
// dashboard MUST refuse any AST shape the backend would reject, so we
// pin the contract here. Happy-path coverage rides on generator.test.js
// (the generator's output is fed through validateAst).

import { describe, expect, it } from 'vitest'

import { validateAst } from './validator'

const _ok = (ast) => expect(validateAst(ast).ok).toBe(true)
const _errors = (ast) => {
  const r = validateAst(ast)
  expect(r.ok).toBe(false)
  return r.errors
}

describe('validateAst - happy path', () => {
  it('accepts a minimal program with one rule', () => {
    _ok({
      type: 'program',
      id: 'p',
      rules: [
        {
          type: 'rule',
          id: 'r1',
          when: { type: 'literal', id: 'lt', value: true },
          then: [
            {
              type: 'assign_points',
              id: 'a1',
              value: { type: 'literal', id: 'lv', value: 5 },
              case_name: 'Reward',
            },
          ],
        },
      ],
    })
  })

  it('accepts a program with only a default branch', () => {
    _ok({
      type: 'program',
      id: 'p',
      rules: [],
      default: {
        type: 'assign_points',
        id: 'd',
        value: { type: 'literal', id: 'ld', value: 1 },
        case_name: 'default',
      },
    })
  })
})

describe('validateAst - root + structure', () => {
  it('rejects non-program root', () => {
    const errs = _errors({ type: 'rule', id: 'x' })
    expect(errs[0].message).toMatch(/AST root must be a 'program'/)
  })

  it('rejects empty program (no rules, no default)', () => {
    const errs = _errors({ type: 'program', id: 'p', rules: [] })
    expect(errs.some((e) => /at least one rule/.test(e.message))).toBe(true)
  })

  it('rejects rule.then that is empty', () => {
    const errs = _errors({
      type: 'program',
      id: 'p',
      rules: [
        {
          type: 'rule',
          id: 'r1',
          when: { type: 'literal', id: 'lt', value: true },
          then: [],
        },
      ],
    })
    expect(errs.some((e) => /non-empty array of statements/.test(e.message))).toBe(true)
  })
})

describe('validateAst - field paths', () => {
  it('rejects field.path outside the whitelist', () => {
    const errs = _errors({
      type: 'program',
      id: 'p',
      rules: [
        {
          type: 'rule',
          id: 'r1',
          when: {
            type: 'compare',
            id: 'c',
            op: '<',
            left: { type: 'field', id: 'f', path: '__proto__' },
            right: { type: 'literal', id: 'l', value: 1 },
          },
          then: [
            {
              type: 'assign_points',
              id: 'a',
              value: { type: 'literal', id: 'lv', value: 1 },
              case_name: 'x',
            },
          ],
        },
      ],
    })
    const fieldErr = errs.find((e) => e.nodeId === 'f')
    expect(fieldErr).toBeDefined()
    expect(fieldErr.message).toMatch(/not in the allowed set/)
  })

  it('accepts data.<key> with alphanumeric+underscore keys', () => {
    _ok({
      type: 'program',
      id: 'p',
      rules: [
        {
          type: 'rule',
          id: 'r1',
          when: {
            type: 'compare',
            id: 'c',
            op: '>',
            left: { type: 'field', id: 'f', path: 'data.my_custom_metric' },
            right: { type: 'literal', id: 'l', value: 0 },
          },
          then: [
            {
              type: 'assign_points',
              id: 'a',
              value: { type: 'literal', id: 'lv', value: 1 },
              case_name: 'x',
            },
          ],
        },
      ],
    })
  })

  it('rejects data path with a dot in the key', () => {
    const errs = _errors({
      type: 'program',
      id: 'p',
      rules: [
        {
          type: 'rule',
          id: 'r1',
          when: {
            type: 'compare',
            id: 'c',
            op: '<',
            left: { type: 'field', id: 'f', path: 'data.nested.field' },
            right: { type: 'literal', id: 'l', value: 1 },
          },
          then: [
            {
              type: 'assign_points',
              id: 'a',
              value: { type: 'literal', id: 'lv', value: 1 },
              case_name: 'x',
            },
          ],
        },
      ],
    })
    expect(errs.find((e) => e.nodeId === 'f')).toBeDefined()
  })
})

describe('validateAst - operators', () => {
  it('rejects arith.op outside ALLOWED_ARITH_OPS', () => {
    const errs = _errors({
      type: 'program',
      id: 'p',
      rules: [
        {
          type: 'rule',
          id: 'r',
          when: { type: 'literal', id: 'lt', value: true },
          then: [
            {
              type: 'assign_points',
              id: 'a',
              value: {
                type: 'arith',
                id: 'ar',
                op: '**',
                left: { type: 'literal', id: 'll', value: 2 },
                right: { type: 'literal', id: 'lr', value: 3 },
              },
              case_name: 'x',
            },
          ],
        },
      ],
    })
    expect(errs.find((e) => e.nodeId === 'ar')).toBeDefined()
  })

  it('accepts min and max as arith ops', () => {
    _ok({
      type: 'program',
      id: 'p',
      rules: [
        {
          type: 'rule',
          id: 'r',
          when: { type: 'literal', id: 'lt', value: true },
          then: [
            {
              type: 'assign_points',
              id: 'a',
              value: {
                type: 'arith',
                id: 'ar',
                op: 'min',
                left: { type: 'literal', id: 'll', value: 5 },
                right: { type: 'literal', id: 'lr', value: 10 },
              },
              case_name: 'x',
            },
          ],
        },
      ],
    })
  })

  it('rejects compare.op outside COMPARE_OPS', () => {
    const errs = _errors({
      type: 'program',
      id: 'p',
      rules: [
        {
          type: 'rule',
          id: 'r',
          when: {
            type: 'compare',
            id: 'c',
            op: '~=',
            left: { type: 'literal', id: 'll', value: 1 },
            right: { type: 'literal', id: 'lr', value: 1 },
          },
          then: [
            {
              type: 'assign_points',
              id: 'a',
              value: { type: 'literal', id: 'lv', value: 1 },
              case_name: 'x',
            },
          ],
        },
      ],
    })
    expect(errs.find((e) => e.nodeId === 'c')).toBeDefined()
  })
})

describe('validateAst - func_call', () => {
  it('rejects unknown func_call name', () => {
    const errs = _errors({
      type: 'program',
      id: 'p',
      rules: [
        {
          type: 'rule',
          id: 'r',
          when: { type: 'literal', id: 'lt', value: true },
          then: [
            {
              type: 'assign_points',
              id: 'a',
              value: {
                type: 'func_call',
                id: 'fc',
                name: 'eval',
                args: [{ type: 'literal', id: 'l', value: 1 }],
              },
              case_name: 'x',
            },
          ],
        },
      ],
    })
    expect(errs.find((e) => e.nodeId === 'fc')).toBeDefined()
  })

  it('rejects wrong arity for int (1 arg expected)', () => {
    const errs = _errors({
      type: 'program',
      id: 'p',
      rules: [
        {
          type: 'rule',
          id: 'r',
          when: { type: 'literal', id: 'lt', value: true },
          then: [
            {
              type: 'assign_points',
              id: 'a',
              value: {
                type: 'func_call',
                id: 'fc',
                name: 'int',
                args: [
                  { type: 'literal', id: 'l1', value: 1 },
                  { type: 'literal', id: 'l2', value: 2 },
                ],
              },
              case_name: 'x',
            },
          ],
        },
      ],
    })
    const e = errs.find((x) => x.nodeId === 'fc')
    expect(e.message).toMatch(/expects 1 args, got 2/)
  })

  it('rejects wrong arity for clamp (3 args expected)', () => {
    const errs = _errors({
      type: 'program',
      id: 'p',
      rules: [
        {
          type: 'rule',
          id: 'r',
          when: { type: 'literal', id: 'lt', value: true },
          then: [
            {
              type: 'assign_points',
              id: 'a',
              value: {
                type: 'func_call',
                id: 'fc',
                name: 'clamp',
                args: [
                  { type: 'literal', id: 'l1', value: 1 },
                  { type: 'literal', id: 'l2', value: 2 },
                ],
              },
              case_name: 'x',
            },
          ],
        },
      ],
    })
    const e = errs.find((x) => x.nodeId === 'fc')
    expect(e.message).toMatch(/expects 3 args, got 2/)
  })
})

describe('validateAst - case_name', () => {
  it('rejects empty case_name', () => {
    const errs = _errors({
      type: 'program',
      id: 'p',
      rules: [
        {
          type: 'rule',
          id: 'r',
          when: { type: 'literal', id: 'lt', value: true },
          then: [
            {
              type: 'assign_points',
              id: 'a',
              value: { type: 'literal', id: 'lv', value: 1 },
              case_name: '',
            },
          ],
        },
      ],
    })
    expect(errs.find((e) => e.nodeId === 'a')).toBeDefined()
  })

  it('rejects case_name with control characters', () => {
    const errs = _errors({
      type: 'program',
      id: 'p',
      rules: [
        {
          type: 'rule',
          id: 'r',
          when: { type: 'literal', id: 'lt', value: true },
          then: [
            {
              type: 'assign_points',
              id: 'a',
              value: { type: 'literal', id: 'lv', value: 1 },
              case_name: 'bad\x00name',
            },
          ],
        },
      ],
    })
    expect(errs.find((e) => e.nodeId === 'a')).toBeDefined()
  })
})

// DSL_EXTEND validation tests.
//
// The validator gained per-section statement whitelisting plus support
// for parent.* field paths (post-only) and the parent_variables map.
// These tests pin the rejection / acceptance contracts the editor
// relies on for immediate designer feedback.

const _ruleWith = (stmt) => ({
  type: 'rule',
  id: `r_${stmt.id}`,
  when: { type: 'literal', id: 'lt', value: true },
  then: [stmt],
})

describe('validateAst - Sprint 7 pre/post sections', () => {
  it('accepts a pre_rules section with a set_data statement', () => {
    _ok({
      type: 'program',
      id: 'p',
      rules: [],
      pre_rules: [
        _ruleWith({
          type: 'set_data',
          id: 'sd',
          key: 'is_first',
          value: { type: 'literal', id: 'lv', value: true },
        }),
      ],
      default: {
        type: 'assign_points',
        id: 'd',
        value: { type: 'literal', id: 'ld', value: 1 },
        case_name: 'fallback',
      },
    })
  })

  it('accepts a post_rules section with set_points reading parent.points', () => {
    _ok({
      type: 'program',
      id: 'p',
      rules: [],
      post_rules: [
        _ruleWith({
          type: 'set_points',
          id: 'sp',
          value: { type: 'field', id: 'fp', path: 'parent.points' },
        }),
      ],
      default: {
        type: 'assign_points',
        id: 'd',
        value: { type: 'literal', id: 'ld', value: 1 },
        case_name: 'fallback',
      },
    })
  })

  it('rejects set_data inside main rules (must be in pre)', () => {
    const errs = _errors({
      type: 'program',
      id: 'p',
      rules: [
        _ruleWith({
          type: 'set_data',
          id: 'sd',
          key: 'x',
          value: { type: 'literal', id: 'lv', value: 1 },
        }),
      ],
    })
    expect(errs.some((e) => /not allowed inside 'rule'/.test(e.message))).toBe(true)
  })

  it('rejects set_points inside pre_rules (must be in post)', () => {
    const errs = _errors({
      type: 'program',
      id: 'p',
      rules: [],
      pre_rules: [
        _ruleWith({
          type: 'set_points',
          id: 'sp',
          value: { type: 'literal', id: 'lv', value: 5 },
        }),
      ],
      default: {
        type: 'assign_points',
        id: 'd',
        value: { type: 'literal', id: 'ld', value: 1 },
        case_name: 'x',
      },
    })
    expect(errs.some((e) => /not allowed inside 'pre'/.test(e.message))).toBe(true)
  })

  it('rejects assign_points inside post_rules (post uses set_points)', () => {
    const errs = _errors({
      type: 'program',
      id: 'p',
      rules: [],
      post_rules: [
        _ruleWith({
          type: 'assign_points',
          id: 'a',
          value: { type: 'literal', id: 'lv', value: 1 },
          case_name: 'x',
        }),
      ],
      default: {
        type: 'assign_points',
        id: 'd',
        value: { type: 'literal', id: 'ld', value: 1 },
        case_name: 'x',
      },
    })
    expect(errs.some((e) => /not allowed inside 'post'/.test(e.message))).toBe(true)
  })

  it('rejects veto outside pre_rules', () => {
    const errs = _errors({
      type: 'program',
      id: 'p',
      rules: [_ruleWith({ type: 'veto', id: 'v', case_name: 'TooEarly' })],
    })
    expect(errs.some((e) => /'veto' is not allowed inside 'rule'/.test(e.message))).toBe(true)
  })

  it('rejects parent.points inside main rules', () => {
    const errs = _errors({
      type: 'program',
      id: 'p',
      rules: [
        {
          type: 'rule',
          id: 'r',
          when: {
            type: 'compare',
            id: 'c',
            op: '>',
            left: { type: 'field', id: 'fp', path: 'parent.points' },
            right: { type: 'literal', id: 'l', value: 0 },
          },
          then: [
            {
              type: 'assign_points',
              id: 'a',
              value: { type: 'literal', id: 'lv', value: 1 },
              case_name: 'x',
            },
          ],
        },
      ],
    })
    expect(errs.some((e) => /only available inside post_rules/.test(e.message))).toBe(true)
  })
})

describe('validateAst - Sprint 7 parent_variables', () => {
  it('accepts a parent_variables map with scalar values', () => {
    _ok({
      type: 'program',
      id: 'p',
      rules: [],
      parent_variables: {
        variable_basic_points: 1,
        variable_bonus_points: 10,
        variable_label: 'override',
      },
      default: {
        type: 'assign_points',
        id: 'd',
        value: { type: 'literal', id: 'ld', value: 1 },
        case_name: 'x',
      },
    })
  })

  it('rejects parent_variables keys not starting with variable_', () => {
    const errs = _errors({
      type: 'program',
      id: 'p',
      rules: [],
      parent_variables: { debug: true },
      default: {
        type: 'assign_points',
        id: 'd',
        value: { type: 'literal', id: 'ld', value: 1 },
        case_name: 'x',
      },
    })
    expect(errs.some((e) => /must start with 'variable_'/.test(e.message))).toBe(true)
  })

  it('rejects non-scalar parent_variables values', () => {
    const errs = _errors({
      type: 'program',
      id: 'p',
      rules: [],
      parent_variables: { variable_basic_points: [1, 2, 3] },
      default: {
        type: 'assign_points',
        id: 'd',
        value: { type: 'literal', id: 'ld', value: 1 },
        case_name: 'x',
      },
    })
    expect(errs.some((e) => /must be a JSON scalar/.test(e.message))).toBe(true)
  })

  it('rejects parent_variables when not an object', () => {
    const errs = _errors({
      type: 'program',
      id: 'p',
      rules: [],
      parent_variables: ['variable_x', 1],
      default: {
        type: 'assign_points',
        id: 'd',
        value: { type: 'literal', id: 'ld', value: 1 },
        case_name: 'x',
      },
    })
    expect(errs.some((e) => /must be an object/.test(e.message))).toBe(true)
  })
})

describe('validateAst - else-if / else branches', () => {
  const assign = (id, caseName) => ({
    type: 'assign_points',
    id,
    value: { type: 'literal', id: `${id}_v`, value: 1 },
    case_name: caseName,
  })
  const ruleWith = (extra) => ({
    type: 'program',
    id: 'p',
    rules: [
      {
        type: 'rule',
        id: 'r1',
        when: { type: 'literal', id: 'w', value: true },
        then: [assign('a1', 'A')],
        ...extra,
      },
    ],
  })

  it('accepts a rule with else_if and else branches', () => {
    _ok(
      ruleWith({
        else_if: [
          {
            when: { type: 'literal', id: 'w2', value: true },
            then: [assign('a2', 'B')],
          },
        ],
        else: [assign('a3', 'C')],
      }),
    )
  })

  it('rejects an else_if branch with an empty then', () => {
    const errs = _errors(
      ruleWith({
        else_if: [{ when: { type: 'literal', id: 'w2', value: true }, then: [] }],
      }),
    )
    expect(errs.some((e) => /non-empty array of statements/.test(e.message))).toBe(true)
  })

  it('rejects an else_if branch missing when', () => {
    const errs = _errors(
      ruleWith({
        else_if: [{ then: [assign('a2', 'B')] }],
      }),
    )
    expect(errs.some((e) => /when is required/.test(e.message))).toBe(true)
  })

  it('rejects an empty else branch', () => {
    const errs = _errors(ruleWith({ else: [] }))
    expect(errs.some((e) => /non-empty array of statements/.test(e.message))).toBe(true)
  })

  it('rejects else_if that is not an array', () => {
    const errs = _errors(ruleWith({ else_if: { when: {}, then: [] } }))
    expect(errs.some((e) => /else_if must be an array/.test(e.message))).toBe(true)
  })

  it('enforces section context inside else / else_if (veto only in pre)', () => {
    // A veto statement is only valid in pre-rules; placing it in a main
    // rule's else branch must be rejected just like in its then.
    const errs = _errors({
      type: 'program',
      id: 'p',
      rules: [
        {
          type: 'rule',
          id: 'r1',
          when: { type: 'literal', id: 'w', value: true },
          then: [assign('a1', 'A')],
          else: [{ type: 'veto', id: 'v1', case_name: 'Nope' }],
        },
      ],
    })
    expect(errs.some((e) => /not allowed inside 'rule'/.test(e.message))).toBe(true)
  })
})
