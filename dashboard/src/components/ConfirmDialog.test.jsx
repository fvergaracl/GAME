// Sprint 6 (CRUD management) — ConfirmDialog tests.
//
// ConfirmDialog is the shared confirm modal behind every destructive or
// irreversible action (delete game/task, revoke key). The risk it carries is
// twofold: a stuck busy state that lets the user dismiss mid-request, and the
// a11y wiring (labelled-by / described-by / aria-busy) that screen readers
// rely on. These tests pin both, plus the basic confirm/cancel callbacks.

import React from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { I18nextProvider } from 'react-i18next'
import { fireEvent, render, screen } from '@testing-library/react'

import i18n from '../i18n'
import ConfirmDialog from './ConfirmDialog'

const renderDialog = (props = {}) =>
  render(
    <I18nextProvider i18n={i18n}>
      <ConfirmDialog
        visible
        title="Delete this game?"
        message="This is permanent."
        confirmLabel="Yes, delete"
        confirmColor="danger"
        onConfirm={props.onConfirm || vi.fn()}
        onCancel={props.onCancel || vi.fn()}
        {...props}
      />
    </I18nextProvider>,
  )

describe('ConfirmDialog', () => {
  afterEach(() => vi.clearAllMocks())

  it('renders the title and message and wires aria attributes', () => {
    renderDialog()
    const title = screen.getByText('Delete this game?')
    expect(title).toHaveAttribute('id', 'confirm-dialog-title')

    const body = screen.getByText('This is permanent.')
    expect(body).toHaveAttribute('id', 'confirm-dialog-body')
    expect(body).toHaveAttribute('aria-busy', 'false')
  })

  it('fires onConfirm and onCancel from the footer buttons', () => {
    const onConfirm = vi.fn()
    const onCancel = vi.fn()
    renderDialog({ onConfirm, onCancel })

    fireEvent.click(screen.getByRole('button', { name: 'Yes, delete' }))
    expect(onConfirm).toHaveBeenCalledTimes(1)

    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(onCancel).toHaveBeenCalledTimes(1)
  })

  it('blocks dismissal and disables actions while busy', () => {
    const onConfirm = vi.fn()
    const onCancel = vi.fn()
    renderDialog({ busy: true, onConfirm, onCancel })

    const cancel = screen.getByRole('button', { name: 'Cancel' })
    // While busy the confirm button also renders a spinner whose
    // visually-hidden "Loading…" text joins its accessible name.
    const confirm = screen.getByRole('button', { name: /Yes, delete/i })
    expect(cancel).toBeDisabled()
    expect(confirm).toBeDisabled()

    // Clicking the disabled cancel must not slip through the busy guard.
    fireEvent.click(cancel)
    expect(onCancel).not.toHaveBeenCalled()

    expect(screen.getByText('This is permanent.')).toHaveAttribute('aria-busy', 'true')
  })
})
