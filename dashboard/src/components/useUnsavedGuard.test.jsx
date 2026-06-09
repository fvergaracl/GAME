// Sprint 6 (CRUD management) - useUnsavedGuard tests.
//
// The guard is one decision shared by all five management form modals, so a
// regression here silently breaks "discard changes?" everywhere at once.
// These pin the truth table: blocked swallows the close, clean closes
// straight through, and dirty defers to window.confirm.

import React from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { I18nextProvider } from 'react-i18next'
import { renderHook } from '@testing-library/react'

import i18n from '../i18n'
import useUnsavedGuard from './useUnsavedGuard'

const wrapper = ({ children }) => <I18nextProvider i18n={i18n}>{children}</I18nextProvider>

const run = (opts) => {
  const { result } = renderHook(() => useUnsavedGuard(opts), { wrapper })
  result.current()
}

describe('useUnsavedGuard', () => {
  afterEach(() => vi.restoreAllMocks())

  it('swallows the close while blocked, even when clean', () => {
    const onClose = vi.fn()
    const confirmSpy = vi.spyOn(window, 'confirm')
    run({ dirty: false, blocked: true, onClose })
    expect(onClose).not.toHaveBeenCalled()
    expect(confirmSpy).not.toHaveBeenCalled()
  })

  it('closes straight through when not dirty', () => {
    const onClose = vi.fn()
    const confirmSpy = vi.spyOn(window, 'confirm')
    run({ dirty: false, blocked: false, onClose })
    expect(onClose).toHaveBeenCalledTimes(1)
    expect(confirmSpy).not.toHaveBeenCalled()
  })

  it('closes when dirty and the user confirms the discard', () => {
    const onClose = vi.fn()
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    run({ dirty: true, blocked: false, onClose })
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('keeps the modal open when dirty and the user cancels the discard', () => {
    const onClose = vi.fn()
    vi.spyOn(window, 'confirm').mockReturnValue(false)
    run({ dirty: true, blocked: false, onClose })
    expect(onClose).not.toHaveBeenCalled()
  })
})
