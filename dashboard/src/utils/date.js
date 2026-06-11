// Centralised date formatting so views don't each redefine the same
// "no value -> dash, otherwise localise" helper. Both formatters use the
// browser's default locale for now; when dates get internationalised this
// is the single place to thread the active i18n locale through.

// Date only (no time-of-day). Empty or unparseable input renders as a dash.
export const formatDate = (value) => {
  if (!value) return '-'
  const d = new Date(value)
  return Number.isNaN(d.getTime()) ? '-' : d.toLocaleDateString()
}

// Date + time-of-day. Empty or unparseable input renders as a dash.
export const formatDateTime = (value) => {
  if (!value) return '-'
  const d = new Date(value)
  return Number.isNaN(d.getTime()) ? '-' : d.toLocaleString()
}
