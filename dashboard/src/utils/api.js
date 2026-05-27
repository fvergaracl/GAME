import keycloak from '../keycloak'

const API_URL = import.meta.env.VITE_GAME_API_URL

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
