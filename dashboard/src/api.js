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

// ---------------------------------------------------------------------------
// Exports (/v1/exports/*)
//
// These endpoints are admin-only and return streaming responses. We can't
// use a plain `<a href download>` because the request must carry a Bearer
// token, so we fetch the body as a Blob and synthesise the download client
// side. Errors are surfaced as thrown Error objects so the calling view can
// render a CAlert without parsing axios internals.
// ---------------------------------------------------------------------------

const EXPORT_DATASETS = ['users', 'user-points', 'user-interactions', 'wallet-transactions']

export const downloadExport = async ({
  dataset,
  format,
  externalGameId,
  externalTaskId,
  dateFrom,
  dateTo,
  limit,
}) => {
  if (!EXPORT_DATASETS.includes(dataset)) {
    throw new Error(`Unknown dataset: ${dataset}`)
  }
  const params = new URLSearchParams()
  params.set('format', format)
  if (limit) params.set('limit', String(limit))
  if (externalGameId) params.set('externalGameId', externalGameId)
  if (externalTaskId) params.set('externalTaskId', externalTaskId)
  if (dateFrom) params.set('dateFrom', new Date(dateFrom).toISOString())
  if (dateTo) params.set('dateTo', new Date(dateTo).toISOString())

  const response = await apiClient.get(`/exports/${dataset}?${params.toString()}`, {
    responseType: 'blob',
  })

  // axios sets response.data to a Blob; pull filename out of
  // Content-Disposition so the user gets the server-suggested name.
  const disposition = response.headers['content-disposition'] || ''
  const match = disposition.match(/filename="?([^";]+)"?/i)
  const fallback = `${dataset}.${format}`
  const filename = match ? match[1] : fallback

  const blobUrl = window.URL.createObjectURL(response.data)
  const link = document.createElement('a')
  link.href = blobUrl
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(blobUrl)
  return { filename, size: response.data.size }
}

export const getExportHistory = async ({ scope = 'mine', limit = 50 } = {}) => {
  const params = new URLSearchParams({ scope, limit: String(limit) })
  return getRequest(`/exports/history?${params.toString()}`)
}


