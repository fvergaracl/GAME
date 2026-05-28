// Tests for the guided-simulation helpers that power the "Test strategy"
// panel: which accumulated fields a strategy reads, and how each run's
// mockState is derived (single run vs. cumulative submissions).

import { describe, expect, it } from 'vitest'

import { buildMockState, collectUsedFieldPaths, usedAccumulationFields } from './simFields'

// A program that reads user.measurements_count (inside a compare) and
// task.measurements_count (inside an arithmetic node), plus a data.* and
// a static id field that must NOT surface as an accumulated input.
const SAMPLE_AST = {
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
        left: { type: 'field', id: 'f1', path: 'user.measurements_count' },
        right: { type: 'literal', id: 'l', value: 3 },
      },
      then: [
        {
          type: 'assign_points',
          id: 'a',
          value: {
            type: 'arith',
            id: 'ar',
            op: '+',
            args: [
              { type: 'field', id: 'f2', path: 'task.measurements_count' },
              { type: 'field', id: 'f3', path: 'data.foo' },
            ],
          },
          case_name: 'default',
        },
      ],
    },
  ],
  default: {
    type: 'assign_points',
    id: 'd',
    value: { type: 'field', id: 'f4', path: 'externalUserId' },
    case_name: 'fallback',
  },
}

describe('collectUsedFieldPaths', () => {
  it('finds field paths nested in when/then/arith/compare/default', () => {
    const paths = collectUsedFieldPaths(SAMPLE_AST)
    expect(paths.has('user.measurements_count')).toBe(true)
    expect(paths.has('task.measurements_count')).toBe(true)
    expect(paths.has('data.foo')).toBe(true)
    expect(paths.has('externalUserId')).toBe(true)
  })

  it('returns an empty set for an AST with no field nodes', () => {
    const ast = {
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
              value: { type: 'literal', id: 'v', value: 10 },
              case_name: 'default',
            },
          ],
        },
      ],
    }
    expect(collectUsedFieldPaths(ast).size).toBe(0)
  })
})

describe('usedAccumulationFields', () => {
  it('returns only analytics fields, excluding data.* and static ids', () => {
    const fields = usedAccumulationFields(SAMPLE_AST)
    const paths = fields.map((m) => m.path)
    expect(paths).toContain('user.measurements_count')
    expect(paths).toContain('task.measurements_count')
    expect(paths).not.toContain('data.foo')
    expect(paths).not.toContain('externalUserId')
  })

  it('preserves catalog order', () => {
    const fields = usedAccumulationFields(SAMPLE_AST)
    expect(fields.map((m) => m.path)).toEqual([
      'user.measurements_count',
      'task.measurements_count',
    ])
  })
})

describe('buildMockState', () => {
  const fieldValues = {
    'user.measurements_count': { value: 2, step: 1 },
    'all.avg_time': { value: 30, step: 0 },
  }
  const usedPaths = ['user.measurements_count', 'all.avg_time']

  it('emits only used analytics paths with finite values', () => {
    expect(buildMockState(fieldValues, usedPaths, 0)).toEqual({
      'user.measurements_count': 2,
      'all.avg_time': 30,
    })
  })

  it('ignores non-accumulation paths even if present in usedPaths', () => {
    const mock = buildMockState(
      { ...fieldValues, 'data.foo': { value: 9, step: 1 } },
      [...usedPaths, 'data.foo'],
      0,
    )
    expect(mock).not.toHaveProperty('data.foo')
  })

  it('skips fields with non-numeric values', () => {
    const mock = buildMockState(
      { 'user.measurements_count': { value: '', step: 1 } },
      ['user.measurements_count'],
      0,
    )
    expect(mock).toEqual({})
  })

  it('applies step*runIndex for cumulative runs', () => {
    // count field grows by its step each run; the time field (step 0)
    // stays fixed across submissions.
    expect(buildMockState(fieldValues, usedPaths, 3)).toEqual({
      'user.measurements_count': 5,
      'all.avg_time': 30,
    })
  })

  it('treats string-encoded inputs as numbers', () => {
    const mock = buildMockState(
      { 'task.measurements_count': { value: '4', step: '2' } },
      ['task.measurements_count'],
      2,
    )
    expect(mock).toEqual({ 'task.measurements_count': 8 })
  })
})
