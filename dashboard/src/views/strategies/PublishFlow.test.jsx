// Sprint 11 - editor publish/lifecycle flow tests.
//
// The full StrategyEditor mounts Blockly, so a head-on integration
// test there would pull in 1.5MB of canvas code we don't need to
// exercise here. Instead we cover the two pieces of the publish flow
// that are independently mountable (and historically untested):
//
//   * ``StrategyVersionHistoryModal``  - the rollback control plane
//     that re-publishes an older version and archives the current one.
//     Admin-gated, with a confirmation step.
//   * ``StrategyPickerModal``           - used by the editor's parent
//     picker (DSL_EXTEND) and by the assignments view. Verifies the
//     custom-vs-built-in tabs and the onSelect contract.
//
// Together they exercise the publish flow as users encounter it:
// listing the right candidates, gating the destructive CTA, and
// confirming before mutating production assignments.

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

vi.mock('../../api', () => ({
  listStrategyVersions: vi.fn(),
  rollbackStrategy: vi.fn(),
  listBuiltInStrategies: vi.fn(),
  listCustomStrategies: vi.fn(),
}))

vi.mock('./glossary/GlossaryHint', () => ({
  default: () => null,
}))

const importMockedApi = async () => await import('../../api')

const flushMicrotasks = () =>
  new Promise((resolve) => setTimeout(resolve, 0))

// ---- StrategyVersionHistoryModal ---------------------------------------

const VERSIONS_FIXTURE = [
  {
    id: 'sid-v1',
    version: 1,
    status: 'ARCHIVED',
    created_at: '2026-01-10T00:00:00Z',
    createdBy: 'felipe',
    astJson: { rules: [{ id: 'r1' }] },
  },
  {
    id: 'sid-v2',
    version: 2,
    status: 'PUBLISHED',
    created_at: '2026-02-10T00:00:00Z',
    createdBy: 'felipe',
    astJson: { rules: [{ id: 'r1' }, { id: 'r2' }] },
  },
]

describe('StrategyVersionHistoryModal - publish/rollback flow', () => {
  beforeEach(async () => {
    const api = await importMockedApi()
    api.listStrategyVersions.mockResolvedValue(VERSIONS_FIXTURE)
    api.rollbackStrategy.mockResolvedValue({
      id: 'sid-v1',
      version: 1,
      status: 'PUBLISHED',
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  const renderModal = async (props = {}) => {
    const { default: StrategyVersionHistoryModal } = await import(
      './StrategyVersionHistoryModal'
    )
    const utils = render(
      <I18nextProvider i18n={i18n}>
        <ToastProvider autohideMs={0}>
          <StrategyVersionHistoryModal
            visible
            strategyId="sid-v1"
            onClose={() => {}}
            isAdmin
            onRollbackDone={() => {}}
            {...props}
          />
        </ToastProvider>
      </I18nextProvider>,
    )
    await waitFor(() => {
      expect(screen.queryByText(/Historial de versiones/i)).not.toBeNull()
    })
    return utils
  }

  // ``v1`` text shows up in the list-group AND in the two diff
  // <select> dropdowns ("v1 · ARCHIVED"), so we always resolve the
  // clickable list-group item directly (CListGroupItem maps to <li>
  // in CoreUI 5; the ``component`` prop isn't forwarded to ``as``).
  const findVersionButton = async (label) => {
    await waitFor(() => {
      expect(screen.getAllByText(label).length).toBeGreaterThan(0)
    })
    const matches = screen.getAllByText(label)
    const item = matches
      .map((el) => el.closest('.list-group-item'))
      .filter(Boolean)[0]
    if (!item) throw new Error(`Couldn't find list-group item for ${label}`)
    return item
  }

  it('lists every version with its lifecycle status badge', async () => {
    await renderModal()
    expect(await findVersionButton('v1')).toBeTruthy()
    expect(await findVersionButton('v2')).toBeTruthy()
    expect(screen.getAllByText('ARCHIVED').length).toBeGreaterThan(0)
    expect(screen.getAllByText('PUBLISHED').length).toBeGreaterThan(0)
  })

  it('hides the rollback CTA for non-admin sessions', async () => {
    await renderModal({ isAdmin: false })
    fireEvent.click(await findVersionButton('v1'))
    expect(screen.queryByRole('button', { name: /Hacer rollback/i })).toBeNull()
  })

  it('shows a confirmation before applying rollback', async () => {
    await renderModal()
    fireEvent.click(await findVersionButton('v1'))
    fireEvent.click(screen.getByRole('button', { name: /Hacer rollback a v1/i }))
    expect(screen.getByText(/Vas a re-publicar/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Sí, hacer rollback/i })).toBeInTheDocument()
  })

  it('calls rollbackStrategy when admin confirms', async () => {
    const api = await importMockedApi()
    const onDone = vi.fn()
    await renderModal({ onRollbackDone: onDone })
    fireEvent.click(await findVersionButton('v1'))
    fireEvent.click(screen.getByRole('button', { name: /Hacer rollback a v1/i }))
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /Sí, hacer rollback/i }))
      await flushMicrotasks()
    })
    expect(api.rollbackStrategy).toHaveBeenCalledWith('sid-v1', 1)
    await waitFor(() => {
      expect(onDone).toHaveBeenCalled()
    })
  })

  it('surfaces a localised error when rollback fails', async () => {
    const api = await importMockedApi()
    api.rollbackStrategy.mockRejectedValueOnce({
      response: { status: 409, data: { detail: 'Another rollback in progress.' } },
    })
    await renderModal()
    fireEvent.click(await findVersionButton('v1'))
    fireEvent.click(screen.getByRole('button', { name: /Hacer rollback a v1/i }))
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /Sí, hacer rollback/i }))
      await flushMicrotasks()
    })
    await waitFor(() => {
      expect(screen.getByText('Another rollback in progress.')).toBeInTheDocument()
    })
  })
})

// ---- StrategyPickerModal -----------------------------------------------

describe('StrategyPickerModal - picker contract', () => {
  beforeEach(async () => {
    const api = await importMockedApi()
    api.listBuiltInStrategies.mockResolvedValue([
      { id: 'default', name: 'Default points', description: 'Built-in' },
    ])
    api.listCustomStrategies.mockResolvedValue([
      {
        id: 'strat-c',
        name: 'Custom challenge',
        version: 2,
        type: 'DSL_FULL',
        description: 'Realm-local',
      },
    ])
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  const renderPicker = async (props = {}) => {
    const { default: StrategyPickerModal } = await import('./StrategyPickerModal')
    const onSelect = vi.fn()
    const onClose = vi.fn()
    const utils = render(
      <I18nextProvider i18n={i18n}>
        <ToastProvider autohideMs={0}>
          <StrategyPickerModal
            visible
            currentStrategyId="default"
            onClose={onClose}
            onSelect={onSelect}
            {...props}
          />
        </ToastProvider>
      </I18nextProvider>,
    )
    await waitFor(() => {
      expect(screen.getByText('Default points')).toBeInTheDocument()
    })
    return { ...utils, onSelect, onClose }
  }

  it('shows the current strategy with an "Actual" badge and a disabled CTA', async () => {
    await renderPicker()
    expect(screen.getByText('Actual')).toBeInTheDocument()
    // The "Usar" button on the active row is replaced by "Ya asignada".
    expect(screen.getByRole('button', { name: /Ya asignada/i })).toBeDisabled()
  })

  it('exposes the custom strategies under the Custom tab', async () => {
    await renderPicker()
    // Click the Custom tab to reveal the custom rows.
    fireEvent.click(screen.getByText(/Custom \(tu realm\)/))
    expect(screen.getByText('Custom challenge')).toBeInTheDocument()
    expect(screen.getByText('v2')).toBeInTheDocument()
  })

  it('invokes onSelect with the encoded id on click', async () => {
    const { onSelect, onClose } = await renderPicker()
    fireEvent.click(screen.getByText(/Custom \(tu realm\)/))
    const useBtn = screen.getByRole('button', { name: /^Usar$/ })
    fireEvent.click(useBtn)
    expect(onSelect).toHaveBeenCalledWith('custom:strat-c')
    expect(onClose).toHaveBeenCalled()
  })
})
