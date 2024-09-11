import axios from 'axios'
import keycloak from './keycloak'
// Base configuration for Axios
const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
    accept: 'application/json',
  },
})

apiClient.interceptors.request.use(
  (config) => {
    let token = null
    if (keycloak.authenticated) {
      token = keycloak.token
      config.headers
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  },
)

export const postRequest = async (url, data) => {
  try {
    const response = await apiClient.post(url, data)
    return response.data
  } catch (error) {
    console.error('POST request failed:', error)
    throw error
  }
}

export const getRequest = async (url) => {
  try {
    const response = await apiClient.get(url)
    return response.data
  } catch (error) {
    console.error('GET request failed:', error)
    throw error
  }
}

export const patchRequest = async (url, data) => {
  try {
    const response = await apiClient.patch(url, data)
    return response.data
  } catch (error) {
    console.error('PATCH request failed:', error)
    throw error
  }
}

export const createApiKey = async (client, description) => {
  const data = { client, description }
  return postRequest('/apikey/create', data)
}

export const getApiKeys = async () => {
  return getRequest('/apikey')
}
