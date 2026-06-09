// Sprint 6 (CRUD management) - TaskFormModal validation + submit tests.
//
// externalTaskId stays immutable after creation, but PATCH accepts
// { strategyId, status, params }. These tests pin the create-mode slug
// validation and payload, the edit-mode "no changes → don't call the API"
// short-circuit (PATCH 409s on an empty body, so the modal must close instead
// of submitting nothing), and that editing params sends the full set with
// existing rows' ids preserved.

import React from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { I18nextProvider } from 'react-i18next'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'

import i18n from '../../../i18n'
import ToastProvider from '../../../components/Toast'

vi.mock('../../../api', () => ({
  createTask: vi.fn(),
  updateTask: vi.fn(),
  listBuiltInStrategies: vi.fn(),
  listCustomStrategies: vi.fn(),
}))

const importApi = async () => await import('../../../api')

const renderModal = async (props = {}) => {
  const { default: TaskFormModal } = await import('./TaskFormModal')
  return render(
    <I18nextProvider i18n={i18n}>
      <ToastProvider>
        <TaskFormModal
          visible
          mode="create"
          gameId="game-1"
          onClose={props.onClose || vi.fn()}
          onSaved={props.onSaved || vi.fn()}
          {...props}
        />
      </ToastProvider>
    </I18nextProvider>,
  )
}

describe('TaskFormModal', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('en')
    const api = await importApi()
    api.listBuiltInStrategies.mockResolvedValue([])
    api.listCustomStrategies.mockResolvedValue([])
    api.createTask.mockResolvedValue({ id: 't1' })
    api.updateTask.mockResolvedValue({ id: 't1' })
  })

  afterEach(() => {
    vi.clearAllMocks()
    vi.restoreAllMocks()
  })

  it('rejects an invalid slug on create', async () => {
    const api = await importApi()
    await renderModal()
    const input = await screen.findByLabelText('Task external ID')

    fireEvent.change(input, { target: { value: 'a b' } }) // space is invalid
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    expect(await screen.findByText(/Use 3 to 60 characters/i)).toBeInTheDocument()
    expect(api.createTask).not.toHaveBeenCalled()
  })

  it('creates a task with the trimmed external id', async () => {
    const api = await importApi()
    const onSaved = vi.fn()
    const onClose = vi.fn()
    await renderModal({ onSaved, onClose })
    const input = await screen.findByLabelText('Task external ID')

    fireEvent.change(input, { target: { value: 'task-login' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => {
      expect(api.createTask).toHaveBeenCalledWith('game-1', { externalTaskId: 'task-login' })
    })
    expect(onSaved).toHaveBeenCalled()
    expect(onClose).toHaveBeenCalled()
  })

  it('closes without calling the API when an edit changes nothing', async () => {
    const api = await importApi()
    const onClose = vi.fn()
    const task = {
      id: 't-uuid-1',
      externalTaskId: 'task-login',
      strategy: { id: 'default' },
      taskParams: [],
    }
    await renderModal({ mode: 'edit', task, onClose })

    // Wait for the edit form (the readonly-id note only renders in edit mode).
    await screen.findByText(/can't be changed when editing/i)
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(onClose).toHaveBeenCalled())
    expect(api.updateTask).not.toHaveBeenCalled()
  })

  it('sends the full param set with existing ids when editing params', async () => {
    const api = await importApi()
    const onSaved = vi.fn()
    const task = {
      id: 't-uuid-1',
      externalTaskId: 'task-login',
      strategy: { id: 'default' },
      status: 'open',
      taskParams: [{ id: 'param-1', key: 'bonus', value: 20 }],
    }
    await renderModal({ mode: 'edit', task, onSaved })

    await screen.findByText(/can't be changed when editing/i)

    // Add a second param row and fill it; the existing row is left untouched.
    fireEvent.click(screen.getByRole('button', { name: 'Add parameter' }))
    const valueInputs = screen.getAllByLabelText('Value')
    const keyInputs = screen.getAllByLabelText('Key')
    fireEvent.change(keyInputs[1], { target: { value: 'penalty' } })
    fireEvent.change(valueInputs[1], { target: { value: '5' } })

    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => {
      expect(api.updateTask).toHaveBeenCalledWith('game-1', 't-uuid-1', {
        params: [
          { id: 'param-1', key: 'bonus', value: 20 },
          { key: 'penalty', value: 5 },
        ],
      })
    })
    expect(onSaved).toHaveBeenCalled()
  })
})
