// Sprint 11 — StrategyLibraryView integration tests.
//
// The library is the discoverability surface (Sprint 2) and the entry
// point to the publish/archive lifecycle from outside the editor
// (Sprint 3 actions). Until now it shipped without component-level
// tests, so a regression in the row actions or filter wiring went
// unnoticed until the user discovered it. These tests exercise the
// view end-to-end with a mocked API module.
//
// Mocking strategy:
//   * Stub the api module so each test controls the rows returned.
//   * Stub keycloak so the admin gate is testable both ways.
//   * Stub the version-history + usage modals (they own their own
//     fetches; we just want to assert they're opened with the right
//     target).
//   * react-joyride is rendered through OnboardingTour. It renders
//     nothing until ``runRequest`` flips, so it stays inert here.

import React, { Suspense } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { I18nextProvider } from 'react-i18next'
import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from '@testing-library/react'

import i18n from '../../i18n'
import ToastProvider from '../../components/Toast'

// ---- Module mocks -------------------------------------------------------

vi.mock('../../api', () => ({
  listCustomStrategies: vi.fn(),
  listBuiltInStrategies: vi.fn(),
  getCustomStrategy: vi.fn(),
  importCustomStrategy: vi.fn(),
  publishCustomStrategy: vi.fn(),
  archiveCustomStrategy: vi.fn(),
}))

// Default keycloak shape: non-admin. Individual tests can override
// the token to simulate an admin session.
vi.mock('../../keycloak', () => ({
  default: { token: null, authenticated: false },
}))

// History + usage modals own large internal fetch graphs. They're
// rendered by the view but stubbed here so the integration test stays
// scoped to the library's own logic (open/close + target id wiring).
vi.mock('./StrategyVersionHistoryModal', () => ({
  default: ({ visible, strategyId, onClose }) =>
    visible ? (
      <div data-testid="version-history-modal">
        history:{strategyId}
        <button type="button" onClick={onClose}>close-history</button>
      </div>
    ) : null,
}))

vi.mock('./StrategyUsageModal', () => ({
  default: ({ visible, strategyId, strategyName, onClose }) =>
    visible ? (
      <div data-testid="usage-modal">
        usage:{strategyId}:{strategyName}
        <button type="button" onClick={onClose}>close-usage</button>
      </div>
    ) : null,
}))

// react-joyride pulls in a non-trivial DOM measurement code path. The
// OnboardingTour wrapper is responsible for gating it; here we replace
// it wholesale so the tests focus on the table.
vi.mock('./OnboardingTour', () => ({
  default: () => null,
}))

// GlossaryHint renders into a real provider in the app, but the lazy
// glossary loader and CModal portal it pulls in are noise for our
// asserts. A trivial stub keeps the tree shallow.
vi.mock('./glossary/GlossaryHint', () => ({
  default: () => null,
}))

// ---- Helpers ------------------------------------------------------------

const navigateSpy = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => navigateSpy,
  }
})

const importMockedApi = async () => await import('../../api')
const importMockedKeycloak = async () => (await import('../../keycloak')).default

const STRATEGIES_FIXTURE = [
  {
    id: 'strat-1',
    name: 'Speed bonus',
    description: 'Reward fast submissions',
    type: 'DSL_FULL',
    status: 'DRAFT',
    version: 1,
    parentStrategyId: null,
    created_at: '2026-03-01T10:00:00Z',
    createdBy: 'felipe@deusto.es',
  },
  {
    id: 'strat-2',
    name: 'Onboarding boost',
    description: 'First-week multiplier',
    type: 'DSL_EXTEND',
    status: 'PUBLISHED',
    version: 4,
    parentStrategyId: 'default',
    created_at: '2026-04-12T10:00:00Z',
    createdBy: 'felipe@deusto.es',
  },
]

const adminToken = (() => {
  // Decoded by isCurrentUserAdmin via atob on the middle segment.
  const payload = {
    resource_access: { account: { roles: ['AdministratorGAME'] } },
  }
  return ['h', btoa(JSON.stringify(payload)), 's'].join('.')
})()

const renderView = async ({ isAdmin = false } = {}) => {
  const keycloak = await importMockedKeycloak()
  keycloak.token = isAdmin ? adminToken : null
  // Lazy-load the view so the api mock is already registered when the
  // module evaluates its imports at the top level.
  const { default: StrategyLibraryView } = await import('./StrategyLibraryView')
  const utils = render(
    <I18nextProvider i18n={i18n}>
      <ToastProvider autohideMs={0}>
        <MemoryRouter initialEntries={['/strategies/library']}>
          <Suspense fallback={<div>loading…</div>}>
            <StrategyLibraryView />
          </Suspense>
        </MemoryRouter>
      </ToastProvider>
    </I18nextProvider>,
  )
  // The view fires two parallel requests on mount. Wait until the
  // skeleton clears and the first row renders before asserting.
  await waitFor(() => {
    expect(screen.queryByText('Speed bonus')).not.toBeNull()
  })
  return utils
}

const flushMicrotasks = () =>
  new Promise((resolve) => setTimeout(resolve, 0))

// CDropdown renders every menu item eagerly, so per-row queries must
// be scoped inside the row that owns the dropdown. ``getRowMenuItem``
// finds the named row by visible label, then grabs the dropdown item
// inside its actions cell.
const getRowMenuItem = (rowLabel, itemLabel) => {
  const cell = screen.getByText(rowLabel).closest('tr')
  if (!cell) throw new Error(`Row "${rowLabel}" not found`)
  return within(cell).getByText(itemLabel)
}

// ---- Tests --------------------------------------------------------------

describe('StrategyLibraryView', () => {
  beforeEach(async () => {
    const api = await importMockedApi()
    api.listCustomStrategies.mockResolvedValue(STRATEGIES_FIXTURE)
    api.listBuiltInStrategies.mockResolvedValue([
      { id: 'default', name: 'Default points', description: '' },
    ])
    api.getCustomStrategy.mockImplementation(async (id) => {
      const row = STRATEGIES_FIXTURE.find((s) => s.id === id)
      return { ...row, astJson: { type: 'PROGRAM' }, blocklyXml: '<xml/>' }
    })
    api.importCustomStrategy.mockResolvedValue({
      id: 'strat-copy',
      name: 'Speed bonus (copia)',
      version: 1,
    })
    api.publishCustomStrategy.mockResolvedValue({
      id: 'strat-1',
      name: 'Speed bonus',
      version: 1,
      status: 'PUBLISHED',
    })
    api.archiveCustomStrategy.mockResolvedValue({
      id: 'strat-2',
      name: 'Onboarding boost',
      version: 4,
      status: 'ARCHIVED',
    })
    navigateSpy.mockClear()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('renders rows and resolves the parent label via the built-in index', async () => {
    await renderView()
    expect(screen.getByText('Speed bonus')).toBeInTheDocument()
    expect(screen.getByText('Onboarding boost')).toBeInTheDocument()
    // Parent id "default" should resolve to its human name from the
    // builtIn index — not the raw id.
    expect(screen.getByText('Default points')).toBeInTheDocument()
    // Version column.
    expect(screen.getByText('v1')).toBeInTheDocument()
    expect(screen.getByText('v4')).toBeInTheDocument()
  })

  it('filters by status via a server-side re-query', async () => {
    const api = await importMockedApi()
    await renderView()
    // First mount fires one call with no status filter.
    expect(api.listCustomStrategies).toHaveBeenCalledTimes(1)
    expect(api.listCustomStrategies).toHaveBeenLastCalledWith({
      status: undefined,
      type: undefined,
      limit: 200,
    })
    // The status select is the first <select> in the filters form.
    // We avoid getByLabelText because the form's label/control wiring
    // uses a sibling pattern, not htmlFor.
    const selects = document.querySelectorAll('select')
    const statusSelect = selects[0]
    api.listCustomStrategies.mockResolvedValueOnce([STRATEGIES_FIXTURE[1]])
    await act(async () => {
      fireEvent.change(statusSelect, { target: { value: 'PUBLISHED' } })
    })
    await waitFor(() => {
      expect(api.listCustomStrategies).toHaveBeenLastCalledWith({
        status: 'PUBLISHED',
        type: undefined,
        limit: 200,
      })
    })
  })

  it('search filters rows client-side without re-querying', async () => {
    const api = await importMockedApi()
    await renderView()
    const searchInput = screen.getByPlaceholderText(/Nombre de la estrategia/i)
    const callsBefore = api.listCustomStrategies.mock.calls.length
    await act(async () => {
      fireEvent.change(searchInput, { target: { value: 'onboarding' } })
    })
    // Speed bonus filtered out, onboarding stays.
    await waitFor(() => {
      expect(screen.queryByText('Speed bonus')).toBeNull()
    })
    expect(screen.getByText('Onboarding boost')).toBeInTheDocument()
    expect(api.listCustomStrategies.mock.calls.length).toBe(callsBefore)
  })

  it('opens the editor when the row "Abrir" button is clicked', async () => {
    await renderView()
    const openButtons = screen.getAllByRole('button', { name: /Abrir/i })
    fireEvent.click(openButtons[0])
    expect(navigateSpy).toHaveBeenCalledWith('/strategies/editor/strat-1')
  })

  it('hides Publicar/Archivar for non-admins', async () => {
    await renderView({ isAdmin: false })
    // Open the first row's action dropdown.
    const actionToggles = screen.getAllByRole('button', { name: /Acciones/i })
    fireEvent.click(actionToggles[0])
    expect(screen.queryByText('Publicar')).toBeNull()
    expect(screen.queryByText('Archivar')).toBeNull()
  })

  it('publishes a draft and surfaces success feedback', async () => {
    const api = await importMockedApi()
    await renderView({ isAdmin: true })
    // Row 1 is a DRAFT — admin should see Publicar in its dropdown.
    fireEvent.click(getRowMenuItem('Speed bonus', 'Publicar'))
    // Confirmation modal pops; click "Sí, publicar".
    const confirmBtn = await screen.findByRole('button', { name: /Sí, publicar/i })
    await act(async () => {
      fireEvent.click(confirmBtn)
      await flushMicrotasks()
    })
    expect(api.publishCustomStrategy).toHaveBeenCalledWith('strat-1')
    await waitFor(() => {
      // The inline CAlert + the toast both render the same message —
      // assert via ``getAllByText`` so the dual render is intentional.
      expect(
        screen.getAllByText(/publicada \(v1\)\. Ahora es la versión en producción\./i)
          .length,
      ).toBeGreaterThan(0)
    })
  })

  it('falls back to extractError when publish fails', async () => {
    const api = await importMockedApi()
    api.publishCustomStrategy.mockRejectedValueOnce({
      response: { status: 400, data: { detail: 'AST validation failed.' } },
    })
    await renderView({ isAdmin: true })
    fireEvent.click(getRowMenuItem('Speed bonus', 'Publicar'))
    const confirmBtn = await screen.findByRole('button', { name: /Sí, publicar/i })
    await act(async () => {
      fireEvent.click(confirmBtn)
      await flushMicrotasks()
    })
    await waitFor(() => {
      // CAlert + toast — both render the extractError output.
      expect(screen.getAllByText('AST validation failed.').length).toBeGreaterThan(0)
    })
  })

  it('opens history modal with the correct strategy id', async () => {
    await renderView()
    fireEvent.click(getRowMenuItem('Onboarding boost', 'Ver historial'))
    const modal = await screen.findByTestId('version-history-modal')
    expect(within(modal).getByText('history:strat-2')).toBeInTheDocument()
  })

  it('opens "where used" modal with the row id and name', async () => {
    await renderView()
    fireEvent.click(getRowMenuItem('Speed bonus', '¿Dónde se usa?'))
    const modal = await screen.findByTestId('usage-modal')
    expect(within(modal).getByText('usage:strat-1:Speed bonus')).toBeInTheDocument()
  })

  it('shows the empty state and CTA when no strategies exist', async () => {
    const api = await importMockedApi()
    api.listCustomStrategies.mockResolvedValue([])
    const { default: StrategyLibraryView } = await import('./StrategyLibraryView')
    render(
      <I18nextProvider i18n={i18n}>
        <ToastProvider autohideMs={0}>
          <MemoryRouter initialEntries={['/strategies/library']}>
            <StrategyLibraryView />
          </MemoryRouter>
        </ToastProvider>
      </I18nextProvider>,
    )
    await waitFor(() => {
      expect(screen.getByText(/Todavía no has creado ninguna estrategia/i)).toBeInTheDocument()
    })
    fireEvent.click(screen.getByRole('button', { name: /Crear mi primera estrategia/i }))
    expect(navigateSpy).toHaveBeenCalledWith('/strategies/editor')
  })
})
