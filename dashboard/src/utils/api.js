import keycloak from '../keycloak'

// Callers build request URLs by concatenation, e.g. `${API_URL}dashboard/summary`,
// so API_URL must end with exactly one slash. The env var is configured without a
// trailing slash (VITE_GAME_API_URL=http://localhost:8000/api/v1), which otherwise
// produces `/api/v1dashboard/...` → 404. Normalise it here so every fetcher caller
// is correct regardless of how the env var is written.
const RAW_API_URL = import.meta.env.VITE_GAME_API_URL || 'http://localhost:8000/api/v1'
const API_URL = RAW_API_URL.endsWith('/') ? RAW_API_URL : `${RAW_API_URL}/`

const fetcher = async (url, options) => {
  if (!keycloak.authenticated) {
    throw new Error('No token found')
  }
  try {
    await keycloak.updateToken(30)
  } catch (e) {
    keycloak.login()
    throw new Error('Keycloak session expired')
  }
  const response = await fetch(url, {
    ...options,
    headers: {
      ...options?.headers,
      Authorization: `Bearer ${keycloak.token}`,
    },
  })
  if (!response.ok) {
    // Mirror the axios error shape ({ response: { status, data } }) so the
    // shared extractError helper can surface the backend's FastAPI ``detail``
    // in read (SWR) views too — previously we only threw statusText, so
    // extractError fell back to the bare HTTP status and the real message was
    // lost on GET endpoints (it was only preserved on axios mutations).
    const data = await response.json().catch(() => null)
    const error = new Error(response.statusText || `HTTP ${response.status}`)
    error.response = { status: response.status, data }
    throw error
  }

  return response
}

export { API_URL, fetcher }
