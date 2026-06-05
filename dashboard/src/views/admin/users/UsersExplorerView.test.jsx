// Sprint 5 (CRUD management) — UsersExplorerView integration tests.
//
// The explorer is read-only, so the regression surface is narrow but the
// state machine isn't: a lookup fans out to two independent endpoints and the
// view has to tell three outcomes apart — both succeed (render), both 404
// (the user doesn't exist), or one 404 (the user exists but has no points /
// no wallet). These tests pin that branching plus the points-total math.

import React from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { I18nextProvider } from 'react-i18next'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'

import i18n from '../../../i18n'

// ---- Module mocks -------------------------------------------------------

vi.mock('../../../api', () => ({
  getUserPoints: vi.fn(),
  getUserWallet: vi.fn(),
}))

const importMockedApi = async () => await import('../../../api')

// ---- Fixtures -----------------------------------------------------------

const POINTS_FIXTURE = [
  {
    externalGameId: 'game-readme-001',
    created_at: '2026-02-10T12:00:00Z',
    task: [
      {
        externalTaskId: 'task-login',
        points: [{ externalUserId: 'user-123', points: 120, timesAwarded: 6 }],
      },
      {
        externalTaskId: 'task-share',
        points: [{ externalUserId: 'user-123', points: 40, timesAwarded: 2 }],
      },
    ],
  },
]

const WALLET_FIXTURE = {
  userId: '8f9d6bc1-2b5f-4cab-b82a-2b0e61bf7c1d',
  wallet: { coinsBalance: 12.5, pointsBalance: 340, conversionRate: 100 },
  walletTransactions: [
    {
      id: 'tx-1',
      created_at: '2026-02-10T14:20:00Z',
      transactionType: 'AssignPoints',
      points: 20,
      coins: 0,
    },
  ],
}

const err404 = () => ({ response: { status: 404 } })

const renderView = async () => {
  const { default: UsersExplorerView } = await import('./UsersExplorerView')
  return render(
    <I18nextProvider i18n={i18n}>
      <UsersExplorerView />
    </I18nextProvider>,
  )
}

const search = async (externalUserId) => {
  fireEvent.change(screen.getByRole('searchbox'), { target: { value: externalUserId } })
  fireEvent.click(screen.getByRole('button', { name: /Search/i }))
}

// ---- Tests --------------------------------------------------------------

describe('UsersExplorerView', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('en')
    const api = await importMockedApi()
    api.getUserPoints.mockResolvedValue(POINTS_FIXTURE)
    api.getUserWallet.mockResolvedValue(WALLET_FIXTURE)
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('shows the empty prompt before any search', async () => {
    await renderView()
    expect(screen.getByText(/Enter an external ID/i)).toBeInTheDocument()
  })

  it('renders points (with the summed total) and wallet for a found user', async () => {
    await renderView()
    await search('user-123')

    await waitFor(() => {
      expect(screen.getByText('task-login')).toBeInTheDocument()
    })
    // Per-task points rows.
    expect(screen.getByText('task-share')).toBeInTheDocument()
    // Total points earned = 120 + 40, summed by the view.
    expect(screen.getByText('160')).toBeInTheDocument()
    // Wallet balances surfaced from the wallet payload.
    expect(screen.getByText('340')).toBeInTheDocument()
    expect(screen.getByText('12.5')).toBeInTheDocument()
    // Internal id + a wallet transaction row.
    expect(screen.getByText(WALLET_FIXTURE.userId)).toBeInTheDocument()
    expect(screen.getByText('AssignPoints')).toBeInTheDocument()
  })

  it('shows "not found" only when both reads 404', async () => {
    const api = await importMockedApi()
    api.getUserPoints.mockRejectedValue(err404())
    api.getUserWallet.mockRejectedValue(err404())

    await renderView()
    await search('ghost-user')

    await waitFor(() => {
      expect(screen.getByText(/No user found with external ID/i)).toBeInTheDocument()
    })
  })

  it('renders the user when points 404 but the wallet exists (no-points state)', async () => {
    const api = await importMockedApi()
    api.getUserPoints.mockRejectedValue(err404())
    api.getUserWallet.mockResolvedValue(WALLET_FIXTURE)

    await renderView()
    await search('user-no-points')

    await waitFor(() => {
      expect(screen.getByText(/hasn't earned any points yet/i)).toBeInTheDocument()
    })
    // Wallet still renders since the user exists.
    expect(screen.getByText('AssignPoints')).toBeInTheDocument()
  })

  it('surfaces a non-404 error instead of the not-found state', async () => {
    const api = await importMockedApi()
    api.getUserPoints.mockRejectedValue({ response: { status: 500, data: { detail: 'boom' } } })
    api.getUserWallet.mockRejectedValue({ response: { status: 500, data: { detail: 'boom' } } })

    await renderView()
    await search('user-err')

    await waitFor(() => {
      expect(screen.getByText('boom')).toBeInTheDocument()
    })
    expect(screen.queryByText(/No user found/i)).toBeNull()
  })
})
