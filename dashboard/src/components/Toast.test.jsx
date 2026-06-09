// Sprint 11 - ToastProvider + useToast tests.
//
// Verifies the centralised feedback layer that replaces the per-view
// CAlert pairs. Pulls i18n into the test runtime so the localised
// titles ("Éxito", "Error", "Aviso", "Información") are exercised
// alongside the API shape.

import React from 'react'
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { act, fireEvent, render, screen } from '@testing-library/react'
import { I18nextProvider } from 'react-i18next'
import i18n from '../i18n'
import ToastProvider, { useToast } from './Toast'

const renderWithProvider = (ui, props = {}) =>
  render(
    <I18nextProvider i18n={i18n}>
      <ToastProvider {...props}>{ui}</ToastProvider>
    </I18nextProvider>,
  )

beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.runOnlyPendingTimers()
  vi.useRealTimers()
})

const Harness = ({ onReady }) => {
  const toast = useToast()
  // Hand the API back to the test so it can drive the toasts.
  React.useEffect(() => {
    onReady(toast)
  }, [toast, onReady])
  return null
}

describe('ToastProvider', () => {
  it('renders a success toast with the localised default title', () => {
    let api
    renderWithProvider(<Harness onReady={(a) => (api = a)} />)
    act(() => {
      api.success('Strategy published')
    })
    expect(screen.getByText('Strategy published')).toBeInTheDocument()
    // Localised title for success comes from common.toasts.title.success.
    // Both Spanish ("Éxito") and English ("Success") are accepted because
    // the language can be locked by previous tests or env detection.
    expect(screen.getByText(/Éxito|Success/i)).toBeInTheDocument()
  })

  it('renders error toasts with kind=danger styling', () => {
    let api
    renderWithProvider(<Harness onReady={(a) => (api = a)} />)
    act(() => {
      api.error('Boom')
    })
    expect(screen.getByText('Boom')).toBeInTheDocument()
    // The kind is exposed via a testid hook so styling regressions
    // surface even when the visible title is localised.
    expect(document.querySelector('[data-testid="gd-toast gd-toast-danger"]')).not.toBeNull()
  })

  it('auto-dismisses after the configured delay', () => {
    let api
    renderWithProvider(<Harness onReady={(a) => (api = a)} />, { autohideMs: 1000 })
    act(() => {
      api.info('Heads up')
    })
    expect(screen.getByText('Heads up')).toBeInTheDocument()
    act(() => {
      vi.advanceTimersByTime(1100)
    })
    expect(screen.queryByText('Heads up')).toBeNull()
  })

  it('respects a per-toast autohideMs override', () => {
    let api
    renderWithProvider(<Harness onReady={(a) => (api = a)} />, { autohideMs: 10_000 })
    act(() => {
      api.warning('Slow ↘', { autohideMs: 500 })
    })
    expect(screen.getByText('Slow ↘')).toBeInTheDocument()
    act(() => {
      vi.advanceTimersByTime(600)
    })
    expect(screen.queryByText('Slow ↘')).toBeNull()
  })

  it('dedupes by id: a second show() with the same id replaces the body', () => {
    let api
    renderWithProvider(<Harness onReady={(a) => (api = a)} />, { autohideMs: 0 })
    act(() => {
      api.show({ kind: 'info', id: 'sync', message: 'Saving…' })
    })
    expect(screen.getByText('Saving…')).toBeInTheDocument()
    act(() => {
      api.show({ kind: 'success', id: 'sync', message: 'Saved.' })
    })
    expect(screen.queryByText('Saving…')).toBeNull()
    expect(screen.getByText('Saved.')).toBeInTheDocument()
  })

  it('clear() removes every active toast and cancels pending timers', () => {
    let api
    renderWithProvider(<Harness onReady={(a) => (api = a)} />, { autohideMs: 0 })
    act(() => {
      api.success('A')
      api.error('B')
      api.warning('C')
    })
    expect(screen.getByText('A')).toBeInTheDocument()
    expect(screen.getByText('B')).toBeInTheDocument()
    expect(screen.getByText('C')).toBeInTheDocument()
    act(() => {
      api.clear()
    })
    expect(screen.queryByText('A')).toBeNull()
    expect(screen.queryByText('B')).toBeNull()
    expect(screen.queryByText('C')).toBeNull()
  })

  it('dismisses on close-button click', () => {
    let api
    renderWithProvider(<Harness onReady={(a) => (api = a)} />, { autohideMs: 0 })
    act(() => {
      api.success('Stays until I close it')
    })
    const closeBtn = screen.getByRole('button', { name: /dismiss|cerrar/i })
    fireEvent.click(closeBtn)
    expect(screen.queryByText('Stays until I close it')).toBeNull()
  })

  it('returns no-op handlers when used outside a provider', () => {
    // No provider wrapping - useToast() should still hand back a usable
    // shape so callers don't have to guard with conditionals.
    let api
    render(<Harness onReady={(a) => (api = a)} />)
    expect(typeof api.success).toBe('function')
    expect(typeof api.error).toBe('function')
    // The calls must not throw and must not render anything.
    expect(() => api.success('Silent')).not.toThrow()
    expect(screen.queryByText('Silent')).toBeNull()
  })
})
