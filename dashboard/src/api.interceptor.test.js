// Tests for the api.js axios *request interceptor* - the auth-critical path
// that api.test.js intentionally leaves inert (it stubs keycloak as
// unauthenticated). Here keycloak is authenticated, so we exercise the three
// behaviours that silently break real logins when they regress:
//   1. silent token refresh (updateToken) + Bearer header injection,
//   2. the login() bounce + request cancellation when the SSO session died,
//   3. the unauthenticated/no-token short-circuits.
//
// api.js registers the interceptor at import time via
// ``apiClient.interceptors.request.use(onFulfilled, onRejected)``; we mock
// axios so that registration is captured and the two handlers can be invoked
// directly with a fake request config.

import { beforeEach, describe, expect, it, vi } from 'vitest'

// Shared keycloak stub - mutated per test to drive each branch. The api.js
// interceptor reads these fields at call time, so reassigning them here is
// enough to switch behaviour.
const keycloak = {
  authenticated: false,
  token: null,
  updateToken: vi.fn(),
  login: vi.fn(),
}
vi.mock('./keycloak', () => ({ default: keycloak }))

vi.mock('axios', () => {
  const client = {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    interceptors: { request: { use: vi.fn() } },
  }
  class Cancel {
    constructor(message) {
      this.message = message
    }
  }
  const axiosMock = { create: vi.fn(() => client), Cancel }
  return { default: axiosMock, ...axiosMock }
})

let onFulfilled
let onRejected

beforeEach(async () => {
  // Fresh module graph each test so the interceptor registers exactly once
  // on a clean client; reset the keycloak stub to its unauthenticated default.
  vi.resetModules()
  keycloak.authenticated = false
  keycloak.token = null
  keycloak.updateToken = vi.fn()
  keycloak.login = vi.fn()

  await import('./api')
  const axios = (await import('axios')).default
  const client = axios.create()
  ;[onFulfilled, onRejected] = client.interceptors.request.use.mock.calls[0]
})

describe('api request interceptor', () => {
  it('passes the request through untouched when unauthenticated', async () => {
    const config = { headers: {} }
    const out = await onFulfilled(config)
    expect(out).toBe(config)
    expect(out.headers.Authorization).toBeUndefined()
    expect(keycloak.updateToken).not.toHaveBeenCalled()
  })

  it('refreshes the token and injects the Bearer header when authenticated', async () => {
    keycloak.authenticated = true
    keycloak.token = 'access-123'
    keycloak.updateToken.mockResolvedValue(true)

    const out = await onFulfilled({ headers: {} })

    expect(keycloak.updateToken).toHaveBeenCalledWith(30)
    expect(out.headers.Authorization).toBe('Bearer access-123')
    expect(keycloak.login).not.toHaveBeenCalled()
  })

  it('bounces to login and cancels the request when the refresh fails', async () => {
    keycloak.authenticated = true
    keycloak.token = 'stale'
    keycloak.updateToken.mockRejectedValue(new Error('SSO session expired'))

    await expect(onFulfilled({ headers: {} })).rejects.toMatchObject({
      message: expect.stringContaining('Keycloak session expired'),
    })
    expect(keycloak.login).toHaveBeenCalledTimes(1)
  })

  it('omits the Authorization header when no token is present after refresh', async () => {
    keycloak.authenticated = true
    keycloak.token = null
    keycloak.updateToken.mockResolvedValue(false)

    const out = await onFulfilled({ headers: {} })

    expect(keycloak.updateToken).toHaveBeenCalledWith(30)
    expect(out.headers.Authorization).toBeUndefined()
  })

  it('propagates request setup errors through the rejection handler', async () => {
    const err = new Error('boom')
    await expect(onRejected(err)).rejects.toBe(err)
  })
})
