// Sprint 6 (CRUD management) — ParamsEditor tests.
//
// ParamsEditor is the controlled {key,value} grid shared by the game and task
// forms. Being controlled, its whole contract is the array it emits via
// onChange: add appends a blank row, edits patch the right index, remove drops
// it. These tests pin that emit shape and the empty-state copy.

import React from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { I18nextProvider } from 'react-i18next'
import { fireEvent, render, screen } from '@testing-library/react'

import i18n from '../i18n'
import ParamsEditor from './ParamsEditor'

const renderEditor = (props = {}) =>
  render(
    <I18nextProvider i18n={i18n}>
      <ParamsEditor value={props.value || []} onChange={props.onChange || vi.fn()} {...props} />
    </I18nextProvider>,
  )

describe('ParamsEditor', () => {
  afterEach(() => vi.clearAllMocks())

  it('shows the empty-state copy with no rows', async () => {
    await i18n.changeLanguage('en')
    renderEditor()
    expect(screen.getByText('No parameters yet.')).toBeInTheDocument()
  })

  it('emits a new blank row when "Add parameter" is clicked', async () => {
    await i18n.changeLanguage('en')
    const onChange = vi.fn()
    renderEditor({ onChange })

    fireEvent.click(screen.getByRole('button', { name: /Add parameter/i }))

    expect(onChange).toHaveBeenCalledTimes(1)
    const emitted = onChange.mock.calls[0][0]
    expect(emitted).toHaveLength(1)
    expect(emitted[0]).toMatchObject({ key: '', value: '' })
  })

  it('patches the edited field by index', async () => {
    await i18n.changeLanguage('en')
    const onChange = vi.fn()
    renderEditor({ value: [{ key: 'color', value: 'red' }], onChange })

    const keyInput = screen.getByDisplayValue('color')
    fireEvent.change(keyInput, { target: { value: 'colour' } })

    expect(onChange).toHaveBeenCalledWith([{ key: 'colour', value: 'red' }])
  })

  it('drops the row on remove', async () => {
    await i18n.changeLanguage('en')
    const onChange = vi.fn()
    renderEditor({ value: [{ key: 'a', value: '1' }], onChange })

    fireEvent.click(screen.getByRole('button', { name: /Remove parameter/i }))

    expect(onChange).toHaveBeenCalledWith([])
  })
})
