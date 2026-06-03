import axios from 'axios'
import keycloak from './keycloak'
// Base configuration for Axios
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_GAME_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
    accept: 'application/json',
  },
})

apiClient.interceptors.request.use(
  async (config) => {
    if (keycloak.authenticated) {
      try {
        // Refresh silently if the access token expires in the next 30s.
        // Returning false means the token was still valid; true means a
        // fresh one was issued.
        await keycloak.updateToken(30)
      } catch (e) {
        // Refresh failed (Keycloak SSO session expired) → bounce the
        // user back through the login flow.
        keycloak.login()
        return Promise.reject(
          new axios.Cancel('Keycloak session expired, redirecting to login'),
        )
      }
      if (keycloak.token) {
        config.headers.Authorization = `Bearer ${keycloak.token}`
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

export const putRequest = async (url, data) => {
  try {
    const response = await apiClient.put(url, data)
    return response.data
  } catch (error) {
    console.error('PUT request failed:', error)
    throw error
  }
}

export const deleteRequest = async (url) => {
  try {
    const response = await apiClient.delete(url)
    return response.data
  } catch (error) {
    console.error('DELETE request failed:', error)
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

// ---------------------------------------------------------------------------
// Custom Strategies (/v1/strategies/custom/*)
//
// Endpoints introduced in Sprints 3-5. The dashboard's Strategy Editor uses
// these to persist Blockly-authored DSL programs and dry-run them via the
// simulate endpoint. All requests are tenant-scoped server-side via the
// Bearer token or X-API-Key header; the realm is never sent from the client.
// ---------------------------------------------------------------------------

export const listCustomStrategies = async ({ status, type, limit = 100 } = {}) => {
  const params = new URLSearchParams({ limit: String(limit) })
  if (status) params.set('status', status)
  if (type) params.set('type', type)
  return getRequest(`/strategies/custom?${params.toString()}`)
}

export const getCustomStrategy = async (id) => {
  return getRequest(`/strategies/custom/${encodeURIComponent(id)}`)
}

export const createCustomStrategy = async (payload) => {
  // payload: { name, description?, type, parentStrategyId?, astJson, blocklyXml? }
  return postRequest('/strategies/custom', payload)
}

export const updateCustomStrategy = async (id, payload) => {
  // PUT mutates a DRAFT in place; on a PUBLISHED row the backend forks
  // a new version+1 draft and returns that one.
  try {
    const response = await apiClient.put(`/strategies/custom/${encodeURIComponent(id)}`, payload)
    return response.data
  } catch (error) {
    console.error('PUT request failed:', error)
    throw error
  }
}

export const publishCustomStrategy = async (id) => {
  return postRequest(`/strategies/custom/${encodeURIComponent(id)}/publish`, {})
}

export const archiveCustomStrategy = async (id) => {
  return postRequest(`/strategies/custom/${encodeURIComponent(id)}/archive`, {})
}

export const simulateCustomStrategy = async (id, request) => {
  // request: { externalGameId, externalTaskId, externalUserId, data?, mockState? }
  return postRequest(`/strategies/custom/${encodeURIComponent(id)}/simulate`, request)
}

// Sprint 5 (fix C7): dry-run an AST supplied inline — no persisted id, so
// "Probar" never spawns an orphan DRAFT and always tests the exact blocks
// on the canvas (unsaved edits included).
// request: { astJson, externalGameId, externalTaskId, externalUserId, data?, mockState? }
export const simulateInlineStrategy = async (request) => {
  return postRequest(`/strategies/custom/simulate`, request)
}

// ---------------------------------------------------------------------------
// Sprint 7 — DSL_EXTEND editor helpers
//
// The editor in DSL_EXTEND mode needs two things from the public
// /v1/strategies endpoints:
//
//   1. The list of built-ins available as parents (populates the
//      "parent picker" dropdown). Reuses the existing GET /strategies
//      list since the payload size is small (~6 built-ins).
//
//   2. A typed schema of a single built-in (populates the dynamic
//      "Parent overrides" toolbox category). The schema endpoint is
//      a Sprint 7 addition that returns variables as an ORDERED LIST
//      with explicit Python type names, so the editor can choose the
//      right input widget per variable.
// ---------------------------------------------------------------------------

export const listBuiltInStrategies = async () => {
  return getRequest('/strategies')
}

export const getStrategySchema = async (id) => {
  return getRequest(`/strategies/${encodeURIComponent(id)}/schema`)
}

// ---------------------------------------------------------------------------
// Sprint 8 — templates + import
//
// Templates are static JSON fixtures shipped with the backend so they can
// share the validator and stay version-pinned to the DSL grammar. The
// "Importar JSON" flow posts a full bundle (the same shape the dashboard
// exports), with the server auto-renaming on name collision so a repeated
// import is idempotent for support engineers.
// ---------------------------------------------------------------------------

export const listStrategyTemplates = async () => {
  return getRequest('/strategies/custom/templates')
}

export const importCustomStrategy = async (bundle) => {
  // bundle: { name, description?, type, parentStrategyId?, astJson,
  //           blocklyXml, exportedAt?, exportedFromVersion? }
  // The server ignores unknown keys (exportedAt, exportedFromVersion) so
  // the round-trip from "Exportar JSON" lands cleanly.
  return postRequest('/strategies/custom/import', bundle)
}

// ---------------------------------------------------------------------------
// Sprint 9 — version history, rollback, and assignment helpers
//
// The history endpoint feeds the StrategyVersionHistoryModal (diff view +
// rollback CTA) and the assignment helpers back the admin "Asignación"
// table. Rollback cascades server-side through Games.strategyId /
// Tasks.strategyId so the UI only needs to re-fetch the assignment table
// after the call returns.
// ---------------------------------------------------------------------------

export const listStrategyVersions = async (id) => {
  return getRequest(`/strategies/custom/${encodeURIComponent(id)}/versions`)
}

export const rollbackStrategy = async (id, version) => {
  return postRequest(
    `/strategies/custom/${encodeURIComponent(id)}/rollback/${encodeURIComponent(version)}`,
    {},
  )
}

export const listGames = async ({
  page = 1,
  pageSize = 100,
  ordering = '-id',
  externalGameId,
  platform,
} = {}) => {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
    ordering,
  })
  // Server-side substring filters (LIKE) so the assignment view searches
  // at scale instead of pulling every game with page_size=all.
  if (externalGameId) params.set('externalGameId', externalGameId)
  if (platform) params.set('platform', platform)
  return getRequest(`/games?${params.toString()}`)
}

// Sprint 6 — reverse lookup: which games/tasks run this exact strategy
// version. Feeds the library's "¿Dónde se usa?" modal (blast-radius
// preview) and the bulk-reassign-all-consumers flow.
export const getStrategyUsage = async (id) => {
  return getRequest(`/strategies/custom/${encodeURIComponent(id)}/usage`)
}

export const listGameTasks = async (gameId) => {
  return getRequest(`/games/${encodeURIComponent(gameId)}/tasks`)
}

export const patchGameStrategy = async (gameId, strategyId) => {
  return patchRequest(`/games/${encodeURIComponent(gameId)}`, { strategyId })
}

export const patchTaskStrategy = async (gameId, taskId, strategyId) => {
  return patchRequest(
    `/games/${encodeURIComponent(gameId)}/tasks/${encodeURIComponent(taskId)}`,
    { strategyId },
  )
}

// ---------------------------------------------------------------------------
// Sprint 0 (CRUD management) — full lifecycle helpers for Games and Tasks.
//
// The dashboard already had read + strategy-reassign helpers (listGames,
// listGameTasks, patchGameStrategy, patchTaskStrategy). These complete the
// CRUD surface the management views need: create / read-one / update (full
// PATCH incl. params) / delete / duplicate, mirroring the backend endpoints
// added in the same sprint (DELETE task, POST game & task duplicate).
// ---------------------------------------------------------------------------

export const getGame = async (gameId) => {
  return getRequest(`/games/${encodeURIComponent(gameId)}`)
}

export const createGame = async (payload) => {
  // payload: { externalGameId, platform, strategyId?, params?: [{key, value}] }
  return postRequest('/games', payload)
}

export const updateGame = async (gameId, payload) => {
  // Full PATCH (not just strategy): any subset of
  // { externalGameId, platform, strategyId, params: [{id, key, value}] }.
  return patchRequest(`/games/${encodeURIComponent(gameId)}`, payload)
}

export const deleteGame = async (gameId) => {
  return deleteRequest(`/games/${encodeURIComponent(gameId)}`)
}

export const duplicateGame = async (gameId, { externalGameId }) => {
  // Deep copy server-side: the new game gets every task + params of the
  // source under the supplied externalGameId.
  return postRequest(`/games/${encodeURIComponent(gameId)}/duplicate`, {
    externalGameId,
  })
}

// Read one task by its EXTERNAL id (the backend GET-by-id route is keyed on
// externalTaskId, not the internal UUID), e.g. to precharge an edit form.
export const getTask = async (gameId, externalTaskId) => {
  return getRequest(
    `/games/${encodeURIComponent(gameId)}/tasks/${encodeURIComponent(externalTaskId)}`,
  )
}

export const createTask = async (gameId, payload) => {
  // payload: { externalTaskId, strategyId?, params?: [{key, value}] }
  return postRequest(`/games/${encodeURIComponent(gameId)}/tasks`, payload)
}

export const bulkCreateTasks = async (gameId, tasks) => {
  // Returns { succesfully_created: [...], failed_to_create: [{task, error}] }
  // so the caller can report a mixed outcome instead of all-or-nothing.
  return postRequest(`/games/${encodeURIComponent(gameId)}/tasks/bulk`, { tasks })
}

export const updateTask = async (gameId, taskId, payload) => {
  // payload: any subset of { strategyId, status }.
  return patchRequest(
    `/games/${encodeURIComponent(gameId)}/tasks/${encodeURIComponent(taskId)}`,
    payload,
  )
}

export const deleteTask = async (gameId, taskId) => {
  return deleteRequest(
    `/games/${encodeURIComponent(gameId)}/tasks/${encodeURIComponent(taskId)}`,
  )
}

export const duplicateTask = async (gameId, taskId, { externalTaskId }) => {
  return postRequest(
    `/games/${encodeURIComponent(gameId)}/tasks/${encodeURIComponent(taskId)}/duplicate`,
    { externalTaskId },
  )
}

// ---------------------------------------------------------------------------
// Sprint 0 (CRUD management) — API key revoke + read-only Users explorer.
// ---------------------------------------------------------------------------

export const deleteApiKey = async (prefix) => {
  // Revoke by public prefix (the safe identifier shown in audit logs).
  // Irreversible server-side — callers must confirm first.
  return deleteRequest(`/apikey/${encodeURIComponent(prefix)}`)
}

export const getUserPoints = async (externalUserId) => {
  return getRequest(`/users/${encodeURIComponent(externalUserId)}/points`)
}

export const getUserWallet = async (externalUserId) => {
  return getRequest(`/users/${encodeURIComponent(externalUserId)}/wallet`)
}

// ---------------------------------------------------------------------------
// Sprint 10 — observability endpoints (metrics + A/B comparison)
//
// The backend aggregates the sampled execution log into a single payload per
// strategy version (status mix, latency percentiles, top errors, case-name
// breakdown, points distribution). The comparison endpoint runs the same
// aggregation against two ids and includes the B - A deltas server-side so
// the UI doesn't need to recompute them.
// ---------------------------------------------------------------------------

const _buildWindowParams = ({ since, until } = {}) => {
  const params = new URLSearchParams()
  if (since) params.set('since', new Date(since).toISOString())
  if (until) params.set('until', new Date(until).toISOString())
  return params
}

export const getStrategyMetrics = async (id, { since, until } = {}) => {
  const params = _buildWindowParams({ since, until })
  const qs = params.toString()
  const path = `/strategies/custom/${encodeURIComponent(id)}/metrics${qs ? `?${qs}` : ''}`
  return getRequest(path)
}

export const compareStrategies = async (idA, idB, { since, until } = {}) => {
  const params = _buildWindowParams({ since, until })
  params.set('a', idA)
  params.set('b', idB)
  return getRequest(`/strategies/custom/compare?${params.toString()}`)
}
