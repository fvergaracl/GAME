// Sprint 6 (CRUD management) — unit tests for the api.js helpers.
//
// The entity helpers (games / tasks / api-keys / users) are thin wrappers
// over axios, but the value they add — and the part that regresses silently
// — is URL construction: path segments are percent-encoded, list filters
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
