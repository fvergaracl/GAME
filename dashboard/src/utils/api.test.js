// Sprint D (F5) - coverage for the SWR fetcher's error shaping.
//
// Before this sprint the fetcher threw ``new Error(response.statusText)`` on a
// non-2xx response. That error had no ``.response``, so the shared
// ``extractError`` helper fell back to the bare HTTP status and the backend's
// FastAPI ``detail`` was lost on read (GET) views - only axios mutations kept
// it. The fetcher now mirrors the axios error shape so ``extractError`` can
// surface the real message everywhere. These tests pin that contract.

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { extractError } from './errors'

// keycloak is stubbed authenticated with a token so the auth guard is inert
// and updateToken resolves without redirecting.
vi.mock('../keycloak', () => ({
  default: {
    authenticated: true,
    token: 'test-token',
    updateToken: vi.fn().mockResolvedValue(true),
    login: vi.fn(),
  },
}))

let fetcher

beforeEach(async () => {
  vi.resetModules()
  ;({ fetcher } = await import('./api'))
})

afterEach(() => {
  vi.restoreAllMocks()
})

const mockFetch = (status, body, { statusText } = {}) => {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: status >= 200 && status < 300,
      status,
      statusText: statusText ?? '',
      json: () =>
        body === undefined ? Promise.reject(new Error('no body')) : Promise.resolve(body),
    }),
  )
}

describe('fetcher error shaping', () => {
  it('attaches an axios-like response with the backend detail on a 422', async () => {
    mockFetch(422, { detail: 'externalGameId already exists' })

    const err = await fetcher('/games').catch((e) => e)

    expect(err.response).toEqual({
      status: 422,
      data: { detail: 'externalGameId already exists' },
    })
    // The whole point: extractError now recovers the real message.
    expect(extractError(err)).toBe('externalGameId already exists')
  })

  it('degrades gracefully when the error body is not JSON', async () => {
    mockFetch(500, undefined, { statusText: 'Internal Server Error' })

    const err = await fetcher('/games').catch((e) => e)

    expect(err.response).toEqual({ status: 500, data: null })
    expect(err.message).toBe('Internal Server Error')
    // No detail to recover → extractError uses the status-based fallback.
    expect(extractError(err)).toContain('500')
  })

  it('returns the response untouched on a 2xx', async () => {
    mockFetch(200, { ok: true })

    const response = await fetcher('/games')

    expect(response.ok).toBe(true)
    expect(response.status).toBe(200)
  })
})
