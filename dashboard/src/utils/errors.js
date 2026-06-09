// Shared error extraction utility.
//
// Before this module each fetching view shipped its own ``extractError``
// (StrategyEditor, StrategyLibraryView, StrategyAssignmentsView,
// StrategyPickerModal, StrategyUsageModal, StrategyVersionHistoryModal,
// ExportData, ExportHistory). They differed in subtle ways (some handled
// 403 specially, some unwrapped Blob bodies, some accepted a t() helper
// for i18n) which made error UX inconsistent and easy to regress.
//
// ``extractError(err, opts)`` is the single canonical helper. It returns
// a human-readable string suitable for a CAlert and never throws.
//
// Options (all optional):
//   * fallback   - string used when no message can be derived.
//   * t          - i18next ``t`` function. When present, special-case
//                  responses (403) and the generic fallback get a
//                  localised wording; without it the wording stays in
//                  Spanish (the source locale).
//   * forbidden  - override message for HTTP 403 (overrides t() default).
//
// Inputs handled:
//   * FastAPI HTTPException bodies - ``{ detail: "..." }`` or
//     ``{ detail: { message: "..." } }``.
//   * ``responseType: 'blob'`` requests where the error body is a Blob
//     the caller can't read synchronously - we degrade to the status
//     code instead of leaking ``[object Blob]``.
//   * Network errors with no ``response`` (axios sets ``err.message``).
//   * Bare ``Error`` instances and arbitrary thrown values.

const UNKNOWN_FALLBACK = 'Error desconocido al contactar el backend.'
const FORBIDDEN_FALLBACK = 'No tienes permiso para esta acción.'

const localise = (t, key, fallback, params) => {
  if (!t) {
    if (params && params.status != null) {
      return fallback.replace('{{status}}', String(params.status))
    }
    return fallback
  }
  return t(`alerts.${key}`, {
    ns: 'common',
    defaultValue: fallback,
    ...(params || {}),
  })
}

// Backwards-compat helper: old callers passed (err, fallbackString) or
// (err, tFunction). Normalise into the new options shape so neither
// pattern breaks.
const normaliseOpts = (opts) => {
  if (opts == null) return {}
  if (typeof opts === 'string') return { fallback: opts }
  if (typeof opts === 'function') return { t: opts }
  return opts
}

export function extractError(err, opts) {
  const { fallback, t, forbidden } = normaliseOpts(opts)

  if (!err) {
    return fallback || localise(t, 'unknownError', UNKNOWN_FALLBACK)
  }

  const response = err.response
  if (response) {
    if (response.status === 403) {
      return forbidden || localise(t, 'forbidden', FORBIDDEN_FALLBACK)
    }

    const data = response.data
    // axios with responseType: 'blob' delivers error bodies as Blobs
    // too, which makes the usual detail unreadable synchronously.
    if (typeof Blob !== 'undefined' && data instanceof Blob) {
      return (
        fallback ||
        localise(t, 'requestFailedStatus', `La petición falló (HTTP ${response.status}).`, {
          status: response.status,
        })
      )
    }

    const detail = data && data.detail
    if (typeof detail === 'string' && detail) return detail
    if (detail && typeof detail === 'object' && typeof detail.message === 'string') {
      return detail.message
    }
    if (typeof data === 'string' && data) return data

    return (
      fallback ||
      localise(t, 'requestFailedStatus', `La petición falló (HTTP ${response.status}).`, {
        status: response.status,
      })
    )
  }

  // No response → axios populates ``err.message`` (e.g. "Network Error").
  if (err.message) return err.message
  if (typeof err === 'string') return err

  return fallback || localise(t, 'unknownError', UNKNOWN_FALLBACK)
}

export default extractError
