// Sprint 11 - StrategyAssignmentsView integration tests.
//
// The assignments view is the only surface that mutates production
// scoring (a PATCH to game.strategyId reshapes points generation for
// every future submission). Until Sprint 11 it shipped without any
// integration coverage, which made the regression risk asymmetric:
// a UI bug here changes how users earn points in production.
//
// These tests cover:
//   * loading state → games render after the mocked fetch resolves
//   * single-game reassignment: picker → confirm → PATCH → row updates
//   * bulk reassignment: select all on page → confirm → PATCH each
//   * "already-assigned" guard: bulk skip is reported, not patched

import React from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { I18nextProvider } from 'react-i18next'
import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react'

import i18n from '../../i18n'
import ToastProvider from '../../components/Toast'

// ---- Module mocks -------------------------------------------------------

vi.mock('../../api', () => ({
  listBuiltInStrategies: vi.fn(),
  listCustomStrategies: vi.fn(),
  listGames: vi.fn(),
  listGameTasks: vi.fn(),
  patchGameStrategy: vi.fn(),
  patchTaskStrategy: vi.fn(),
}))

vi.mock('./OnboardingTour', () => ({
  default: () => null,
}))

vi.mock('./glossary/GlossaryHint', () => ({
  default: () => null,
}))

// StrategyPickerModal owns its own fetches and is exercised separately.
// Here we replace it with a controllable stub so the test can drive
// onSelect directly without simulating the modal UI.
let pickerRecorded = null
vi.mock('./StrategyPickerModal', () => ({
  default: ({ visible, currentStrategyId, onSelect, onClose }) => {
    pickerRecorded = { visible, currentStrategyId, onSelect, onClose }
    if (!visible) return null
    return (
      <div data-testid="picker-modal">
        picker:open
        <button
          type="button"
          onClick={() => {
            onSelect('default')
            onClose()
          }}
        >
          pick-default
        </button>
        <button
          type="button"
          onClick={() => {
            onSelect('custom:strat-a')
            onClose()
          }}
        >
          pick-custom-a
        </button>
      </div>
    )
  },
}))

const importMockedApi = async () => await import('../../api')

// ---- Fixtures -----------------------------------------------------------

const GAMES_FIXTURE = [
  {
    gameId: 'gid-1',
    externalGameId: 'game-readme-001',
    platform: 'web',
    strategyId: 'default',
  },
  {
    gameId: 'gid-2',
    externalGameId: 'game-readme-002',
    platform: 'web',
    strategyId: 'custom:strat-a',
  },
  {
    gameId: 'gid-3',
    externalGameId: 'game-readme-003',
    platform: 'web',
    strategyId: null,
  },
]

const renderView = async () => {
  const { default: StrategyAssignmentsView } = await import('./StrategyAssignmentsView')
  const utils = render(
    <I18nextProvider i18n={i18n}>
      <ToastProvider autohideMs={0}>
        <StrategyAssignmentsView />
      </ToastProvider>
    </I18nextProvider>,
  )
  await waitFor(() => {
    expect(screen.queryByText('game-readme-001')).not.toBeNull()
  })
  return utils
}

const flushMicrotasks = () =>
  new Promise((resolve) => setTimeout(resolve, 0))

// ---- Tests --------------------------------------------------------------

describe('StrategyAssignmentsView', () => {
  beforeEach(async () => {
    pickerRecorded = null
    const api = await importMockedApi()
    api.listBuiltInStrategies.mockResolvedValue([
      { id: 'default', name: 'Default points', description: '' },
    ])
    // The view requests two custom-strategy lists (PUBLISHED + all).
    // Resolve them with the same fixture; the merge step is exercised
    // by the renderStrategyLabel asserts below.
    api.listCustomStrategies.mockResolvedValue([
      {
        id: 'strat-a',
        name: 'Speed bonus',
        version: 3,
        type: 'DSL_FULL',
        status: 'PUBLISHED',
      },
    ])
    api.listGames.mockResolvedValue({
      items: GAMES_FIXTURE,
      search_options: { total_count: 3 },
    })
    api.listGameTasks.mockResolvedValue({ items: [] })
    api.patchGameStrategy.mockResolvedValue({})
    api.patchTaskStrategy.mockResolvedValue({})
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('renders the page of games with their current strategy labels', async () => {
    await renderView()
    expect(screen.getByText('game-readme-001')).toBeInTheDocument()
    expect(screen.getByText('game-readme-002')).toBeInTheDocument()
    expect(screen.getByText('game-readme-003')).toBeInTheDocument()
    // Built-in label resolved via the index.
    expect(screen.getByText('Default points')).toBeInTheDocument()
    // Custom strategy id rendered as "Name vN".
    expect(screen.getByText('Speed bonus v3')).toBeInTheDocument()
  })

  it('debounces the search and re-queries listGames', async () => {
    const api = await importMockedApi()
    await renderView()
    const initialCalls = api.listGames.mock.calls.length
    const search = screen.getByPlaceholderText(/game-readme-001/i)
    await act(async () => {
      fireEvent.change(search, { target: { value: 'foo' } })
    })
    // The debounce is 300ms - wait it out with real timers.
    await waitFor(
      () => {
        expect(api.listGames.mock.calls.length).toBeGreaterThan(initialCalls)
      },
      { timeout: 1500 },
    )
    expect(api.listGames).toHaveBeenLastCalledWith({
      page: 1,
      pageSize: 20,
      externalGameId: 'foo',
    })
  })

  it('opens the picker for a single game and patches on confirm', async () => {
    const api = await importMockedApi()
    await renderView()
    // The "Cambiar" button on the first row opens the picker.
    const changeButtons = screen.getAllByRole('button', { name: /^Cambiar$/ })
    fireEvent.click(changeButtons[0])
    // Picker stub records its props - verify it was opened with the
    // row's current strategyId so the "Actual" badge is correct.
    expect(pickerRecorded.visible).toBe(true)
    expect(pickerRecorded.currentStrategyId).toBe('default')
    // Pick a different strategy; the view should stage a pending
    // confirmation instead of patching immediately.
    await act(async () => {
      fireEvent.click(screen.getByText('pick-custom-a'))
    })
    expect(api.patchGameStrategy).not.toHaveBeenCalled()
    // Confirm modal renders with the target label.
    expect(screen.getByText(/Confirmar reasignación/i)).toBeInTheDocument()
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /^Reasignar$/ }))
      await flushMicrotasks()
    })
    expect(api.patchGameStrategy).toHaveBeenCalledWith('gid-1', 'custom:strat-a')
    await waitFor(() => {
      // The view emits both the inline alert and a toast.
      expect(
        screen.getAllByText(/Estrategia del game actualizada\./).length,
      ).toBeGreaterThan(0)
    })
  })

  it('surfaces a warning when single PATCH fails', async () => {
    const api = await importMockedApi()
    api.patchGameStrategy.mockRejectedValueOnce({
      response: { status: 409, data: { detail: 'Conflict - strategy mid-publish.' } },
    })
    await renderView()
    fireEvent.click(screen.getAllByRole('button', { name: /^Cambiar$/ })[0])
    await act(async () => {
      fireEvent.click(screen.getByText('pick-custom-a'))
    })
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /^Reasignar$/ }))
      await flushMicrotasks()
    })
    await waitFor(() => {
      expect(
        screen.getAllByText('Conflict - strategy mid-publish.').length,
      ).toBeGreaterThan(0)
    })
  })

  it('bulk-reassigns selected games, skipping ones already on the target', async () => {
    const api = await importMockedApi()
    await renderView()
    // Click the "select all on page" checkbox in the header.
    const checkboxes = screen.getAllByRole('checkbox')
    // Index 0 is the header "select all"; the rest are per-row.
    fireEvent.click(checkboxes[0])
    // The bulk action bar should appear with the count.
    expect(screen.getByText(/3 games seleccionados en esta página/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Reasignar seleccionados/i }))
    // Picker stub fires onSelect with 'default'; gid-1 is already on
    // default, so the bulk should only patch gid-2 and gid-3.
    await act(async () => {
      fireEvent.click(screen.getByText('pick-default'))
    })
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /^Reasignar$/ }))
      await flushMicrotasks()
    })
    // 1 game (gid-1) was already on 'default' and should be skipped.
    expect(api.patchGameStrategy).toHaveBeenCalledTimes(2)
    const patchedIds = api.patchGameStrategy.mock.calls.map((c) => c[0]).sort()
    expect(patchedIds).toEqual(['gid-2', 'gid-3'])
    await waitFor(() => {
      expect(
        screen.getAllByText(/2 games reasignados\./).length,
      ).toBeGreaterThan(0)
    })
    // Same message hits both the inline alert and the toast, so accept
    // one-or-more occurrences.
    expect(screen.getAllByText(/1 ya tenían esa estrategia\./).length).toBeGreaterThan(0)
  })

  it('disables paging buttons at the edges', async () => {
    await renderView()
    const prev = screen.getByRole('button', { name: /Anterior/i })
    const next = screen.getByRole('button', { name: /Siguiente/i })
    // total_count=3, pageSize=20 → only one page exists.
    expect(prev).toBeDisabled()
    expect(next).toBeDisabled()
  })
})
