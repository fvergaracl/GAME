// Sprint 9 — coverage for the shared extractError helper. Pins the
// behaviour the per-view duplicates used to provide so the consolidation
// stays a net upgrade (no caller silently loses a special-case message).

import { describe, expect, it, vi } from 'vitest'
import { extractError } from './errors'

describe('extractError', () => {
  it('returns FastAPI detail string when present', () => {
    const err = { response: { data: { detail: 'Validation failed' } } }
    expect(extractError(err)).toBe('Validation failed')
  })

  it('unwraps nested detail.message objects', () => {
    const err = {
      response: { data: { detail: { code: 'foo', message: 'Bad payload' } } },
    }
    expect(extractError(err)).toBe('Bad payload')
  })

  it('falls back to err.message on network errors', () => {
    const err = new Error('Network Error')
    expect(extractError(err)).toBe('Network Error')
  })

  it('honours a string fallback when nothing else is parseable', () => {
    expect(extractError(null, 'Custom fallback')).toBe('Custom fallback')
  })

  it('honours the fallback in the options-object form', () => {
    expect(extractError(null, { fallback: 'Options fallback' })).toBe('Options fallback')
  })

  it('returns a 403-specific message', () => {
    const err = { response: { status: 403, data: {} } }
    expect(extractError(err)).toBe('No tienes permiso para esta acción.')
  })

  it('allows a forbidden override', () => {
    const err = { response: { status: 403, data: {} } }
    const msg = extractError(err, { forbidden: 'Admin only.' })
    expect(msg).toBe('Admin only.')
  })

  it('degrades Blob bodies to a status code', () => {
    const blob = new Blob(['{"detail":"x"}'], { type: 'application/json' })
    const err = { response: { status: 500, data: blob } }
    expect(extractError(err)).toContain('HTTP 500')
  })

  it('uses i18next when a t function is provided (positional form)', () => {
    const t = vi.fn(() => 'Translated unknown')
    const msg = extractError(null, t)
    expect(t).toHaveBeenCalledWith('alerts.unknownError', expect.objectContaining({ ns: 'common' }))
    expect(msg).toBe('Translated unknown')
  })

  it('uses i18next when a t function is provided (options form)', () => {
    const t = vi.fn((key, opts) => `[${key}:${opts.status}]`)
    const err = { response: { status: 502, data: {} } }
    expect(extractError(err, { t })).toBe('[alerts.requestFailedStatus:502]')
  })

  it('prefers an explicit fallback over the generic localised one', () => {
    expect(extractError(null, { fallback: 'pick me', t: () => 'no' })).toBe('pick me')
  })

  it('returns a status-code fallback when there is no detail body', () => {
    const err = { response: { status: 504, data: {} } }
    expect(extractError(err)).toBe('La petición falló (HTTP 504).')
  })

  it('accepts a bare string as the error input', () => {
    expect(extractError('boom')).toBe('boom')
  })

  it('returns the generic Spanish fallback when nothing matches', () => {
    expect(extractError({})).toBe('Error desconocido al contactar el backend.')
  })
})
