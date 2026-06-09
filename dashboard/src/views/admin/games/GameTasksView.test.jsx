// Regression: switching between games keeps GameTasksView mounted (only the
// :gameId route param changes), so per-game state must be reset on gameId
// change. Otherwise the previous game's rows — or an open edit modal — survive
// the navigation and acting on them targets a task from the old game under the
// new gameId, which the backend rejects with a cross-game 404.

import React from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { I18nextProvider } from 'react-i18next'
import { Link, MemoryRouter, Route, Routes } from 'react-router-dom'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'

import i18n from '../../../i18n'
import ToastProvider from '../../../components/Toast'

vi.mock('../../../api', () => ({
  getGame: vi.fn(),
  listGameTasks: vi.fn(),
  listBuiltInStrategies: vi.fn(),
  listCustomStrategies: vi.fn(),
  createTask: vi.fn(),
  updateTask: vi.fn(),
}))

const importApi = async () => await import('../../../api')

const TASK_A = {
  id: 'task-a',
  externalTaskId: 'task-from-a',
  strategy: { id: 'default' },
  status: 'open',
  taskParams: [],
}

const renderView = async () => {
  const { default: GameTasksView } = await import('./GameTasksView')
  return render(
    <I18nextProvider i18n={i18n}>
      <ToastProvider>
        <MemoryRouter initialEntries={['/admin/games/game-A/tasks']}>
          {/* Outside <Routes> so it survives the navigation and can drive it. */}
          <Link to="/admin/games/game-B/tasks">go-to-B</Link>
          <Routes>
            <Route path="/admin/games/:gameId/tasks" element={<GameTasksView />} />
          </Routes>
        </MemoryRouter>
      </ToastProvider>
    </I18nextProvider>,
  )
}

describe('GameTasksView (game switch reset)', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('en')
    const api = await importApi()
    api.getGame.mockResolvedValue({ externalGameId: 'ext' })
    api.listGameTasks.mockImplementation((gameId) =>
      Promise.resolve({ items: gameId === 'game-A' ? [TASK_A] : [] }),
    )
    api.listBuiltInStrategies.mockResolvedValue([])
    api.listCustomStrategies.mockResolvedValue([])
  })

  afterEach(() => {
    vi.clearAllMocks()
    vi.restoreAllMocks()
  })

  it("drops the previous game's rows when navigating to another game", async () => {
    await renderView()
    expect(await screen.findByText('task-from-a')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('link', { name: 'go-to-B' }))

    // game-B has no tasks: the stale row is gone and the empty state shows.
    await waitFor(() =>
      expect(screen.queryByText('task-from-a')).not.toBeInTheDocument(),
    )
    expect(await screen.findByText(/has no tasks yet/i)).toBeInTheDocument()
  })

  it('closes an open edit modal when navigating to another game', async () => {
    await renderView()
    await screen.findByText('task-from-a')

    // Open the row actions menu and click Edit.
    fireEvent.click(screen.getByRole('button', { name: 'Actions' }))
    fireEvent.click(await screen.findByText('Edit'))
    expect(await screen.findByText('Edit task')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('link', { name: 'go-to-B' }))

    // The modal that targeted game-A's task must not linger over game-B.
    await waitFor(() =>
      expect(screen.queryByText('Edit task')).not.toBeInTheDocument(),
    )
  })
})
