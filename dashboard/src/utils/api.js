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
    throw new Error(response.statusText)
  }

  return response
}

export { API_URL, fetcher }
