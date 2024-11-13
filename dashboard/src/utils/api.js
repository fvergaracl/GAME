import keycloak from '../keycloak'

const API_URL = import.meta.env.VITE_GAME_API_URL

const fetcher = async (url, options) => {
  const token = keycloak.token
  if (!token) {
    throw new Error('No token found')
  }
  const response = await fetch(url, {
    ...options,
    headers: {
      ...options?.headers,
      Authorization: `Bearer ${token}`,
    },
  })
  if (!response.ok) {
    throw new Error(response.statusText)
  }

  return response
}

export { API_URL, fetcher }
