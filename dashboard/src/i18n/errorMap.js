// Translate a structured DSL error coming back from the API
// into a localised string.
//
// The backend now emits ``detail`` as either:
//   * a bare string (legacy raises that haven't been migrated)
//   * an object ``{ code, params, message }``
//
// This helper accepts both axios error objects AND the detail body
// directly, so callers can do ``translateDslError(t, axiosError)`` or
// ``translateDslError(t, response.data.detail)`` indistinctly.

import { dslErrorMessage } from './errorCodes'

/**
 * Translate a DSL error into a localised string.
 *
 * @param {Function} t - the i18next ``t`` function from useTranslation()
 * @param {*} source - axios error, error body, or bare string
 * @returns {string|null} localised message, or null if no DSL signal found
 */
export function translateDslError(t, source) {
  if (!source) return null
  const detail = _extractDetail(source)
  if (!detail) return null

  if (typeof detail === 'string') {
    return detail
  }
  if (typeof detail === 'object' && detail.code) {
    return dslErrorMessage(t, detail.code, detail.params, detail.message)
  }
  if (typeof detail === 'object' && detail.message) {
    return detail.message
  }
  return null
}

// Walk the most common shapes axios returns. The caller may hand us:
//   * an axios error with response.data.detail (the FastAPI body)
//   * the response body { detail: ... }
//   * the detail object directly { code, params, ... }
//   * a bare string
function _extractDetail(source) {
  if (typeof source === 'string') return source
  if (typeof source !== 'object') return null
  if (source.response?.data?.detail !== undefined) {
    return source.response.data.detail
  }
  if (source.detail !== undefined) return source.detail
  if (source.code !== undefined) return source
  if (source.message && !source.response) return source.message
  return null
}
