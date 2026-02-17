const DEFAULT_MAX_HISTORY = 10

export const mergeUrl = (baseUrl, path) => {
  const normalizedBase = (baseUrl || '').trim().replace(/\/+$/, '')
  const normalizedPath = (path || '').trim()

  if (!normalizedPath) {
    return normalizedBase
  }

  if (/^https?:\/\//i.test(normalizedPath)) {
    return normalizedPath
  }

  if (!normalizedBase) {
    return normalizedPath
  }

  return `${normalizedBase}/${normalizedPath.replace(/^\/+/, '')}`
}

export const safeParseJson = (rawBody) => {
  const trimmedBody = (rawBody || '').trim()

  if (!trimmedBody) {
    return { ok: true, parsed: null, compact: '', formatted: '' }
  }

  try {
    const parsed = JSON.parse(trimmedBody)
    return {
      ok: true,
      parsed,
      compact: JSON.stringify(parsed),
      formatted: JSON.stringify(parsed, null, 2),
    }
  } catch (_error) {
    return { ok: false, error: 'Invalid JSON body.' }
  }
}

const quoteShellValue = (value) => `'${String(value).replace(/'/g, `'\\''`)}'`

export const buildCurlCommand = ({ url, method, bearerToken, apiKey, body }) => {
  if (!url) {
    return { ok: false, error: 'Base URL and path are empty.' }
  }

  const currentMethod = (method || 'GET').toUpperCase()
  const parts = ['curl', '-X', currentMethod, quoteShellValue(url), '-H', quoteShellValue('Accept: application/json')]

  if ((bearerToken || '').trim()) {
    parts.push('-H', quoteShellValue(`Authorization: Bearer ${bearerToken.trim()}`))
  }

  if ((apiKey || '').trim()) {
    parts.push('-H', quoteShellValue(`X-API-Key: ${apiKey.trim()}`))
  }

  const canSendBody = ['POST', 'PUT', 'PATCH', 'DELETE'].includes(currentMethod)
  const parsedBody = safeParseJson(body)

  if (canSendBody && (body || '').trim()) {
    if (!parsedBody.ok) {
      return { ok: false, error: parsedBody.error }
    }

    parts.push('-H', quoteShellValue('Content-Type: application/json'))
    parts.push('--data', quoteShellValue(parsedBody.compact))
  }

  return { ok: true, command: parts.join(' ') }
}

export const upsertSavedRequest = (savedRequests, requestToStore) => {
  const normalizedName = (requestToStore?.name || '').trim()
  if (!normalizedName) {
    return savedRequests
  }

  const normalizedRequest = {
    ...requestToStore,
    name: normalizedName,
  }

  const withoutPrevious = (savedRequests || []).filter(
    (savedRequest) => savedRequest.name.toLowerCase() !== normalizedName.toLowerCase(),
  )

  return [normalizedRequest, ...withoutPrevious].slice(0, 15)
}

export const pushHistoryEntry = (history, entry, maxHistory = DEFAULT_MAX_HISTORY) =>
  [entry, ...(history || [])].slice(0, maxHistory)

