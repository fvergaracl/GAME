// Sprint 6 (CRUD management) - GameFormModal validation + submit tests.
//
// The form is the only client-side gate on a game's externalGameId (the
// backend re-validates, but a bad slug there is a 422 round-trip the user
// shouldn't need). These tests pin the two react-hook-form rules (required +
// slug pattern), the happy-path create call shape, and the unsaved-changes
// guard that protects typed input on close.

import React from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { I18nextProvider } from 'react-i18next'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'

import i18n from '../../../i18n'
import ToastProvider from '../../../components/Toast'

vi.mock('../../../api', () => ({
  createGame: vi.fn(),
  updateGame: vi.fn(),
  getGame: vi.fn(),
  listBuiltInStrategies: vi.fn(),
  listCustomStrategies: vi.fn(),
}))

const importApi = async () => await import('../../../api')

const renderModal = async (props = {}) => {
  const { default: GameFormModal } = await import('./GameFormModal')
  return render(
    <I18nextProvider i18n={i18n}>
      <ToastProvider>
        <GameFormModal
          visible
          mode="create"
          onClose={props.onClose || vi.fn()}
          onSaved={props.onSaved || vi.fn()}
          {...props}
        />
      </ToastProvider>
    </I18nextProvider>,
  )
}

describe('GameFormModal', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('en')
    const api = await importApi()
    api.listBuiltInStrategies.mockResolvedValue([])
    api.listCustomStrategies.mockResolvedValue([])
    api.createGame.mockResolvedValue({ gameId: 1 })
  })

  afterEach(() => {
    vi.clearAllMocks()
    vi.restoreAllMocks()
  })

  it('renders the create title once strategies resolve', async () => {
    await renderModal()
    expect(await screen.findByText('Create game')).toBeInTheDocument()
    expect(screen.getByLabelText('Game external ID')).toBeInTheDocument()
  })

  it('blocks submit and shows a required error when the id is empty', async () => {
    const api = await importApi()
    await renderModal()
    await screen.findByLabelText('Game external ID')

    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    expect(await screen.findByText('This field is required')).toBeInTheDocument()
    expect(api.createGame).not.toHaveBeenCalled()
  })

  it('rejects an invalid slug', async () => {
    const api = await importApi()
    await renderModal()
    const input = await screen.findByLabelText('Game external ID')

    fireEvent.change(input, { target: { value: 'ab' } }) // too short for {3,60}
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    expect(await screen.findByText(/Use 3 to 60 characters/i)).toBeInTheDocument()
    expect(api.createGame).not.toHaveBeenCalled()
  })

  it('creates a game with the normalised payload and closes', async () => {
    const api = await importApi()
    const onSaved = vi.fn()
    const onClose = vi.fn()
    await renderModal({ onSaved, onClose })
    const input = await screen.findByLabelText('Game external ID')

    fireEvent.change(input, { target: { value: 'valid-game' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => {
      expect(api.createGame).toHaveBeenCalledWith({
        externalGameId: 'valid-game',
        platform: 'web',
        strategyId: 'default',
      })
    })
    expect(onSaved).toHaveBeenCalled()
    expect(onClose).toHaveBeenCalled()
  })

  it('warns before discarding typed input on cancel', async () => {
    const onClose = vi.fn()
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false)
    await renderModal({ onClose })
    const input = await screen.findByLabelText('Game external ID')

    fireEvent.change(input, { target: { value: 'dirty' } })
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))

    expect(confirmSpy).toHaveBeenCalled()
    expect(onClose).not.toHaveBeenCalled() // user declined the discard

    confirmSpy.mockReturnValue(true)
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(onClose).toHaveBeenCalled()
  })
})
