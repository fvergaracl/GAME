// Smoke test for the keycloak singleton. There's no logic to speak of - the
// module just constructs a keycloak-js client from the build-time VITE_*
// env - but pinning the wiring catches a renamed/missing env var or a
// constructor-shape change before it ships a dashboard that can't log in.

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('keycloak-js', () => ({
  default: vi.fn(function Keycloak(config) {
    this.config = config
  }),
}))

describe('keycloak singleton', () => {
  beforeEach(() => {
    vi.resetModules()
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    vi.clearAllMocks()
  })

  it('constructs the client from the VITE_KEYCLOAK_* env vars', async () => {
    vi.stubEnv('VITE_KEYCLOAK_URL', 'https://kc.example.test/')
    vi.stubEnv('VITE_KEYCLOAK_REALM', 'game-realm')
    vi.stubEnv('VITE_KEYCLOAK_CLIENT_ID', 'dashboard-client')

    const Keycloak = (await import('keycloak-js')).default
    const keycloak = (await import('./keycloak')).default

    expect(Keycloak).toHaveBeenCalledTimes(1)
    expect(Keycloak).toHaveBeenCalledWith({
      url: 'https://kc.example.test/',
      realm: 'game-realm',
      clientId: 'dashboard-client',
    })
    expect(keycloak).toBeInstanceOf(Keycloak)
  })
})
