// Unit tests for the api.js helpers.
//
// The entity helpers (games / tasks / api-keys / users) are thin wrappers
// over axios, but the value they add - and the part that regresses silently
// - is URL construction: path segments are percent-encoded, list filters
// become query params, and a few helpers reshape the payload (bulk wraps the
// list in { tasks }, duplicate sends just { externalGameId }). These tests
// pin that contract against the backend routes without a live server.
//
// We mock axios so ``axios.create()`` returns a single shared client whose
// verb methods are spies; every helper unwraps ``response.data``, so the
// mocks resolve ``{ data }`` and we assert both the call and the return.
// keycloak is stubbed unauthenticated so the request interceptor is inert.

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('./keycloak', () => ({
  default: { authenticated: false, token: null },
}))

vi.mock('axios', () => {
  const client = {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    interceptors: { request: { use: vi.fn() } },
  }
  const axiosMock = {
    create: vi.fn(() => client),
    Cancel: class Cancel {},
  }
  return { default: axiosMock, ...axiosMock }
})

// Same singleton client instance api.js captured at import time.
const getClient = async () => {
  const axios = (await import('axios')).default
  return axios.create()
}

let api
let client

beforeEach(async () => {
  api = await import('./api')
  client = await getClient()
  for (const verb of ['get', 'post', 'patch', 'put', 'delete']) {
    client[verb].mockReset()
    client[verb].mockResolvedValue({ data: { ok: true } })
  }
})

afterEach(() => {
  vi.clearAllMocks()
})

describe('Games helpers', () => {
  it('listGames builds the default query string', async () => {
    await api.listGames()
    expect(client.get).toHaveBeenCalledWith('/games?page=1&page_size=100&ordering=-id')
  })

  it('listGames appends externalGameId + platform filters', async () => {
    await api.listGames({ page: 2, pageSize: 20, externalGameId: 'foo', platform: 'web' })
    const url = client.get.mock.calls[0][0]
    expect(url).toContain('page=2')
    expect(url).toContain('page_size=20')
    expect(url).toContain('externalGameId=foo')
    expect(url).toContain('platform=web')
  })

  it('getGame percent-encodes the id and unwraps data', async () => {
    client.get.mockResolvedValue({ data: { gameId: 1 } })
    const result = await api.getGame('a/b')
    expect(client.get).toHaveBeenCalledWith('/games/a%2Fb')
    expect(result).toEqual({ gameId: 1 })
  })

  it('createGame posts the payload to /games', async () => {
    const payload = { externalGameId: 'g1', platform: 'web' }
    await api.createGame(payload)
    expect(client.post).toHaveBeenCalledWith('/games', payload)
  })

  it('updateGame patches /games/{id}', async () => {
    const payload = { platform: 'mobile' }
    await api.updateGame('g1', payload)
    expect(client.patch).toHaveBeenCalledWith('/games/g1', payload)
  })

  it('deleteGame deletes /games/{id}', async () => {
    await api.deleteGame('g1')
    expect(client.delete).toHaveBeenCalledWith('/games/g1')
  })

  it('duplicateGame posts only the new externalGameId', async () => {
    await api.duplicateGame('g1', { externalGameId: 'copy-of-g1' })
    expect(client.post).toHaveBeenCalledWith('/games/g1/duplicate', {
      externalGameId: 'copy-of-g1',
    })
  })
})

describe('Tasks helpers', () => {
  it('getTask encodes both segments', async () => {
    await api.getTask('g 1', 't/1')
    expect(client.get).toHaveBeenCalledWith('/games/g%201/tasks/t%2F1')
  })

  it('createTask posts to the game tasks collection', async () => {
    const payload = { externalTaskId: 't1' }
    await api.createTask('g1', payload)
    expect(client.post).toHaveBeenCalledWith('/games/g1/tasks', payload)
  })

  it('bulkCreateTasks wraps the list in { tasks }', async () => {
    const tasks = [{ externalTaskId: 'a' }, { externalTaskId: 'b' }]
    await api.bulkCreateTasks('g1', tasks)
    expect(client.post).toHaveBeenCalledWith('/games/g1/tasks/bulk', { tasks })
  })

  it('updateTask patches the task route', async () => {
    await api.updateTask('g1', 't1', { status: 'closed' })
    expect(client.patch).toHaveBeenCalledWith('/games/g1/tasks/t1', { status: 'closed' })
  })

  it('deleteTask deletes the task route', async () => {
    await api.deleteTask('g1', 't1')
    expect(client.delete).toHaveBeenCalledWith('/games/g1/tasks/t1')
  })

  it('duplicateTask posts the new externalTaskId', async () => {
    await api.duplicateTask('g1', 't1', { externalTaskId: 'copy-of-t1' })
    expect(client.post).toHaveBeenCalledWith('/games/g1/tasks/t1/duplicate', {
      externalTaskId: 'copy-of-t1',
    })
  })
})

describe('API key + user helpers', () => {
  it('deleteApiKey encodes the prefix', async () => {
    await api.deleteApiKey('pref/ix')
    expect(client.delete).toHaveBeenCalledWith('/apikey/pref%2Fix')
  })

  it('getUserPoints / getUserWallet hit the user sub-routes', async () => {
    await api.getUserPoints('user 1')
    await api.getUserWallet('user 1')
    expect(client.get).toHaveBeenNthCalledWith(1, '/users/user%201/points')
    expect(client.get).toHaveBeenNthCalledWith(2, '/users/user%201/wallet')
  })
})

describe('downloadExport guard', () => {
  it('throws on an unknown dataset before touching the network', async () => {
    await expect(api.downloadExport({ dataset: 'bogus', format: 'csv' })).rejects.toThrow(
      /Unknown dataset/,
    )
    expect(client.get).not.toHaveBeenCalled()
  })
})

describe('generic request wrappers', () => {
  it('postRequest rethrows the underlying error', async () => {
    const boom = new Error('network down')
    client.post.mockRejectedValue(boom)
    await expect(api.postRequest('/x', {})).rejects.toBe(boom)
  })

  it('getRequest returns the response body', async () => {
    client.get.mockResolvedValue({ data: [1, 2, 3] })
    await expect(api.getRequest('/x')).resolves.toEqual([1, 2, 3])
  })
})

describe('downloadExport happy path', () => {
  beforeEach(() => {
    // jsdom doesn't implement object URLs or anchor navigation; stub them so
    // we can assert the client-side download dance without side effects.
    window.URL.createObjectURL = vi.fn(() => 'blob:fake-url')
    window.URL.revokeObjectURL = vi.fn()
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})
  })

  it('streams the blob and takes the filename from Content-Disposition', async () => {
    const blob = new Blob(['a,b\n1,2'], { type: 'text/csv' })
    client.get.mockResolvedValue({
      data: blob,
      headers: { 'content-disposition': 'attachment; filename="users-2024.csv"' },
    })

    const result = await api.downloadExport({ dataset: 'users', format: 'csv', limit: 10 })

    const [url, opts] = client.get.mock.calls[0]
    expect(url).toMatch(/^\/exports\/users\?/)
    expect(url).toContain('format=csv')
    expect(url).toContain('limit=10')
    expect(opts).toEqual({ responseType: 'blob' })
    expect(result).toEqual({ filename: 'users-2024.csv', size: blob.size })
    expect(window.URL.createObjectURL).toHaveBeenCalledWith(blob)
    expect(window.URL.revokeObjectURL).toHaveBeenCalledWith('blob:fake-url')
  })

  it('falls back to "<dataset>.<format>" when no filename header is present', async () => {
    client.get.mockResolvedValue({ data: new Blob(['x']), headers: {} })
    const result = await api.downloadExport({ dataset: 'user-points', format: 'json' })
    expect(result.filename).toBe('user-points.json')
  })

  it('serialises date filters to ISO and threads game/task ids', async () => {
    client.get.mockResolvedValue({ data: new Blob(['x']), headers: {} })
    await api.downloadExport({
      dataset: 'user-interactions',
      format: 'csv',
      externalGameId: 'g1',
      externalTaskId: 't1',
      dateFrom: '2024-01-01',
      dateTo: '2024-02-01',
    })
    const url = client.get.mock.calls[0][0]
    expect(url).toContain('externalGameId=g1')
    expect(url).toContain('externalTaskId=t1')
    expect(url).toContain('dateFrom=2024-01-01T00%3A00%3A00.000Z')
    expect(url).toContain('dateTo=2024-02-01T00%3A00%3A00.000Z')
  })
})

describe('exports history + custom-strategy wrappers', () => {
  it('getExportHistory builds the default scope/limit query', async () => {
    await api.getExportHistory()
    expect(client.get).toHaveBeenCalledWith('/exports/history?scope=mine&limit=50')
  })

  it('getExportHistory honours overrides', async () => {
    await api.getExportHistory({ scope: 'all', limit: 5 })
    expect(client.get).toHaveBeenCalledWith('/exports/history?scope=all&limit=5')
  })

  it('listCustomStrategies appends status/type filters', async () => {
    await api.listCustomStrategies({ status: 'PUBLISHED', type: 'DSL', limit: 25 })
    const url = client.get.mock.calls[0][0]
    expect(url).toContain('/strategies/custom?')
    expect(url).toContain('limit=25')
    expect(url).toContain('status=PUBLISHED')
    expect(url).toContain('type=DSL')
  })

  it('getCustomStrategy / createCustomStrategy', async () => {
    await api.getCustomStrategy('a/b')
    expect(client.get).toHaveBeenCalledWith('/strategies/custom/a%2Fb')
    const payload = { name: 'X', type: 'DSL', astJson: {} }
    await api.createCustomStrategy(payload)
    expect(client.post).toHaveBeenCalledWith('/strategies/custom', payload)
  })

  it('updateCustomStrategy puts and unwraps data', async () => {
    client.put.mockResolvedValue({ data: { id: 'v2' } })
    const result = await api.updateCustomStrategy('s1', { name: 'Y' })
    expect(client.put).toHaveBeenCalledWith('/strategies/custom/s1', { name: 'Y' })
    expect(result).toEqual({ id: 'v2' })
  })

  it('updateCustomStrategy rethrows the underlying error', async () => {
    const boom = new Error('conflict')
    client.put.mockRejectedValue(boom)
    await expect(api.updateCustomStrategy('s1', {})).rejects.toBe(boom)
  })

  it('publish / archive post to the lifecycle routes (encoded id)', async () => {
    await api.publishCustomStrategy('s 1')
    await api.archiveCustomStrategy('s 1')
    expect(client.post).toHaveBeenNthCalledWith(1, '/strategies/custom/s%201/publish', {})
    expect(client.post).toHaveBeenNthCalledWith(2, '/strategies/custom/s%201/archive', {})
  })

  it('simulateCustomStrategy / simulateInlineStrategy', async () => {
    await api.simulateCustomStrategy('s1', { externalUserId: 'u' })
    await api.simulateInlineStrategy({ astJson: {} })
    expect(client.post).toHaveBeenNthCalledWith(1, '/strategies/custom/s1/simulate', {
      externalUserId: 'u',
    })
    expect(client.post).toHaveBeenNthCalledWith(2, '/strategies/custom/simulate', { astJson: {} })
  })

  it('listBuiltInStrategies / getStrategySchema / listStrategyTemplates', async () => {
    await api.listBuiltInStrategies()
    await api.getStrategySchema('default')
    await api.listStrategyTemplates()
    expect(client.get).toHaveBeenNthCalledWith(1, '/strategies')
    expect(client.get).toHaveBeenNthCalledWith(2, '/strategies/default/schema')
    expect(client.get).toHaveBeenNthCalledWith(3, '/strategies/custom/templates')
  })

  it('importCustomStrategy posts the bundle', async () => {
    const bundle = { name: 'n', type: 'DSL', astJson: {} }
    await api.importCustomStrategy(bundle)
    expect(client.post).toHaveBeenCalledWith('/strategies/custom/import', bundle)
  })

  it('listStrategyVersions / rollbackStrategy / getStrategyUsage', async () => {
    await api.listStrategyVersions('s1')
    await api.rollbackStrategy('s1', 3)
    await api.getStrategyUsage('s1')
    expect(client.get).toHaveBeenNthCalledWith(1, '/strategies/custom/s1/versions')
    expect(client.post).toHaveBeenCalledWith('/strategies/custom/s1/rollback/3', {})
    expect(client.get).toHaveBeenNthCalledWith(2, '/strategies/custom/s1/usage')
  })
})

describe('api keys, assignment + observability wrappers', () => {
  it('createApiKey / getApiKeys', async () => {
    await api.createApiKey('web', 'desc')
    await api.getApiKeys()
    expect(client.post).toHaveBeenCalledWith('/apikey/create', {
      client: 'web',
      description: 'desc',
    })
    expect(client.get).toHaveBeenCalledWith('/apikey')
  })

  it('patchGameStrategy / patchTaskStrategy / listGameTasks', async () => {
    await api.patchGameStrategy('g1', 's1')
    await api.patchTaskStrategy('g1', 't1', 's1')
    await api.listGameTasks('g1')
    expect(client.patch).toHaveBeenNthCalledWith(1, '/games/g1', { strategyId: 's1' })
    expect(client.patch).toHaveBeenNthCalledWith(2, '/games/g1/tasks/t1', { strategyId: 's1' })
    expect(client.get).toHaveBeenCalledWith('/games/g1/tasks')
  })

  it('getStrategyMetrics omits the window when no range is given', async () => {
    await api.getStrategyMetrics('s1')
    expect(client.get).toHaveBeenCalledWith('/strategies/custom/s1/metrics')
  })

  it('getStrategyMetrics serialises the since/until window', async () => {
    await api.getStrategyMetrics('s1', { since: '2024-01-01', until: '2024-02-01' })
    const url = client.get.mock.calls[0][0]
    expect(url).toContain('/strategies/custom/s1/metrics?')
    expect(url).toContain('since=2024-01-01T00%3A00%3A00.000Z')
    expect(url).toContain('until=2024-02-01T00%3A00%3A00.000Z')
  })

  it('compareStrategies sets a + b ids and the window', async () => {
    await api.compareStrategies('s1', 's2', { since: '2024-01-01' })
    const url = client.get.mock.calls[0][0]
    expect(url).toContain('/strategies/custom/compare?')
    expect(url).toContain('a=s1')
    expect(url).toContain('b=s2')
    expect(url).toContain('since=2024-01-01T00%3A00%3A00.000Z')
  })
})
