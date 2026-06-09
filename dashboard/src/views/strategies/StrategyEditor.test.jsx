// Regression net for the editor's load/hydration path.
//
// Locks in the fix: Blockly is injected exactly once per editing
// session and saved content hydrates that same instance instead of being
// disposed and re-injected blank (the "editor opens empty when I edit a
// strategy" bug - see the diagnosis doc, F1/F2).

import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { I18nextProvider } from 'react-i18next'
import { act, fireEvent, render, waitFor } from '@testing-library/react'
import * as Blockly from 'blockly'

import i18n from '../../i18n'
import ToastProvider from '../../components/Toast'
import { registerDslBlocks } from './blocks'
import { workspaceToAst } from './dsl/generator'
import { validateAst } from './dsl/validator'

// ``inject`` renders to a canvas jsdom can't measure, so we fake only it:
// it returns a real headless ``Blockly.Workspace`` (so serialization and
// ``workspaceToAst`` run for real) with the rendered-only methods stubbed
// and ``dispose`` spied, to prove the instance is never torn down.
vi.mock('blockly', async (importOriginal) => {
  const actual = await importOriginal()
  return {
    ...actual,
    inject: vi.fn(() => {
      const ws = new actual.Workspace()
      ws.updateToolbox = vi.fn()
      ws.registerToolboxCategoryCallback = vi.fn()
      ws.centerOnBlock = vi.fn()
      vi.spyOn(ws, 'dispose')
      return ws
    }),
  }
})

vi.mock('../../api', () => ({
  getCustomStrategy: vi.fn(),
  listBuiltInStrategies: vi.fn(),
  getStrategySchema: vi.fn(),
  createCustomStrategy: vi.fn(),
  updateCustomStrategy: vi.fn(),
  importCustomStrategy: vi.fn(),
  publishCustomStrategy: vi.fn(),
  archiveCustomStrategy: vi.fn(),
  simulateInlineStrategy: vi.fn(),
}))

vi.mock('../../keycloak', () => ({
  default: { token: null, authenticated: false },
}))

// Decorative / heavy lazy children - stubbed to keep the tree shallow.
vi.mock('./glossary/GlossaryHint', () => ({ default: () => null }))
vi.mock('./EditorTour', () => ({ default: () => null }))
vi.mock('./TemplatePickerModal', () => ({ default: () => null }))
vi.mock('./SimulationScenarios', () => ({ default: () => null }))
vi.mock('./SimulationRunsChart', () => ({ default: () => null }))
vi.mock('./SimulationTracePanel', () => ({ default: () => null }))
vi.mock('./StrategyVersionHistoryModal', () => ({ default: () => null }))

// Serialized state for the canonical "BasicEngagement" rule (the scenario
// generator.test.js pins), in the modern Blockly JSON format the editor
// persists and feeds back through ``pendingImportBundle``:
//   when task.measurements_count < 2  then assign_points 1, "BasicEngagement"
const buildBasicEngagementBlocklyXml = () => {
  const ws = new Blockly.Workspace()
  try {
    const rule = ws.newBlock('gd_rule', 'r1')

    const compare = ws.newBlock('gd_compare', 'c1')
    compare.setFieldValue('<', 'OP')
    const field = ws.newBlock('gd_field', 'f1')
    field.setFieldValue('task.measurements_count', 'PATH')
    const threshold = ws.newBlock('gd_literal_number', 'l1')
    threshold.setFieldValue('2', 'VALUE')
    compare.getInput('LEFT').connection.connect(field.outputConnection)
    compare.getInput('RIGHT').connection.connect(threshold.outputConnection)
    rule.getInput('WHEN').connection.connect(compare.outputConnection)

    const assign = ws.newBlock('gd_assign_points', 'a1')
    assign.setFieldValue('BasicEngagement', 'CASE_NAME')
    const points = ws.newBlock('gd_literal_number', 'lv1')
    points.setFieldValue('1', 'VALUE')
    assign.getInput('VALUE').connection.connect(points.outputConnection)
    rule.getInput('THEN').connection.connect(assign.previousConnection)

    return JSON.stringify(Blockly.serialization.workspaces.save(ws))
  } finally {
    ws.dispose()
  }
}

const BASIC_ENGAGEMENT_AST = {
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
}

const makeRow = (overrides = {}) => ({
  id: 'strat-1',
  name: 'Speed bonus',
  description: 'Reward fast submissions',
  type: 'DSL_FULL',
  status: 'DRAFT',
  version: 1,
  parentStrategyId: null,
  blocklyXml: buildBasicEngagementBlocklyXml(),
  astJson: BASIC_ENGAGEMENT_AST,
  ...overrides,
})

const renderEditor = async (row) => {
  const api = await import('../../api')
  api.listBuiltInStrategies.mockResolvedValue([])
  api.getCustomStrategy.mockResolvedValue(row)
  const { default: StrategyEditor } = await import('./StrategyEditor')
  return render(
    <I18nextProvider i18n={i18n}>
      <ToastProvider autohideMs={0}>
        <MemoryRouter initialEntries={['/strategies/editor/strat-1']}>
          <Routes>
            <Route path="/strategies/editor/:id" element={<StrategyEditor />} />
          </Routes>
        </MemoryRouter>
      </ToastProvider>
    </I18nextProvider>,
  )
}

// The single workspace the editor holds (the bug created three).
const survivingWorkspace = () => {
  expect(Blockly.inject).toHaveBeenCalledTimes(1)
  return Blockly.inject.mock.results[0].value
}

const waitForHydration = async (ws) =>
  waitFor(() => expect(ws.getAllBlocks(false).length).toBeGreaterThan(0))

describe('StrategyEditor - load/hydration', () => {
  beforeAll(() => {
    // The editor re-registers on mount; the call is idempotent.
    registerDslBlocks()
  })

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('F1 - editing an existing strategy hydrates the single workspace (no blank canvas)', async () => {
    await renderEditor(makeRow())

    await waitFor(() => expect(Blockly.inject).toHaveBeenCalled())
    const ws = survivingWorkspace()
    await waitForHydration(ws)

    // The buggy code injected three times and kept an empty WS-3.
    expect(Blockly.inject).toHaveBeenCalledTimes(1)
    expect(ws.dispose).not.toHaveBeenCalled()
    expect(workspaceToAst(ws)).toEqual(BASIC_ENGAGEMENT_AST)
  })

  it('F2 - switching FULL↔EXTEND mid-edit keeps the blocks (toolbox swaps in place)', async () => {
    await renderEditor(makeRow())

    await waitFor(() => expect(Blockly.inject).toHaveBeenCalled())
    const ws = survivingWorkspace()
    await waitForHydration(ws)
    const blocksBefore = ws.getAllBlocks(false).length

    // Selected by id so the assertion doesn't hinge on the UI language.
    const extendRadio = document.getElementById('mode-extend')
    expect(extendRadio).toBeTruthy()
    await act(async () => {
      fireEvent.click(extendRadio)
    })

    // The mode change must swap the toolbox in place, not dispose + re-inject.
    await waitFor(() => expect(ws.updateToolbox).toHaveBeenCalled())
    expect(Blockly.inject).toHaveBeenCalledTimes(1)
    expect(ws.dispose).not.toHaveBeenCalled()
    expect(ws.getAllBlocks(false).length).toBe(blocksBefore)
  })

  it('round-trips a serialized blocklyXml back to the expected AST through the editor load path', async () => {
    const row = makeRow()
    await renderEditor(row)

    await waitFor(() => expect(Blockly.inject).toHaveBeenCalled())
    const ws = survivingWorkspace()
    await waitForHydration(ws)

    const ast = workspaceToAst(ws)
    expect(ast).toEqual(BASIC_ENGAGEMENT_AST)
    expect(ast).toEqual(row.astJson)
    expect(validateAst(ast).ok).toBe(true)
  })
})

// Robust loading (F4) and data-loss guards (F3).
describe('StrategyEditor - robust load / data-loss guards', () => {
  beforeAll(() => {
    registerDslBlocks()
  })

  beforeEach(() => {
    vi.clearAllMocks()
  })

  // The static portion of the localised "load failed" message (everything
  // before the interpolated error), so the assertion is language-agnostic.
  const ERROR_SENTINEL = ' ERR '
  const loadFailedPrefix = i18n
    .t('alerts.loadFailed', { ns: 'editor', error: ERROR_SENTINEL })
    .split(ERROR_SENTINEL)[0]

  it('F4 - a corrupt blocklyXml surfaces a clear error instead of a silent blank canvas', async () => {
    await renderEditor(makeRow({ blocklyXml: '{ this is : not valid json' }))

    await waitFor(() => expect(Blockly.inject).toHaveBeenCalled())
    const ws = survivingWorkspace()

    // The error must reach the user...
    await waitFor(() => expect(document.body.textContent).toContain(loadFailedPrefix))
    // ...without tearing down or duplicating the workspace, and the parse
    // failure (caught before ``clear``) leaves the canvas empty, not crashed.
    expect(Blockly.inject).toHaveBeenCalledTimes(1)
    expect(ws.dispose).not.toHaveBeenCalled()
    expect(ws.getAllBlocks(false)).toHaveLength(0)
  })

  it('F3 - loading a DRAFT leaves it clean so an untouched canvas is never autosaved over', async () => {
    const api = await import('../../api')
    await renderEditor(makeRow())

    await waitFor(() => expect(Blockly.inject).toHaveBeenCalled())
    const ws = survivingWorkspace()
    await waitForHydration(ws)

    // A freshly-loaded, untouched strategy must read as clean: no "unsaved
    // changes" badge. A wrong (e.g. empty) baseline here would mark it dirty
    // and arm the autosave that previously clobbered saved blocks.
    const unsavedLabel = i18n.t('header.unsaved', { ns: 'editor' })
    await waitFor(() => expect(workspaceToAst(ws)).toEqual(BASIC_ENGAGEMENT_AST))
    expect(document.body.textContent).not.toContain(unsavedLabel)
    // The clean load must not have triggered any persistence on its own.
    expect(api.updateCustomStrategy).not.toHaveBeenCalled()
    expect(api.createCustomStrategy).not.toHaveBeenCalled()
  })
})
