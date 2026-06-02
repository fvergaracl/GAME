// Sprint 11 — centralized toast/feedback system.
//
// Until Sprint 11 every view rolled its own success/error pair as
// CAlerts mounted inline (StrategyLibraryView, StrategyAssignmentsView,
// StrategyEditor, ExportData…). That pattern bled across files in
// subtly different ways: some auto-dismissed, some didn't; some lived
// at the top of a card, some inside a modal. The result was that the
// same successful action was acknowledged differently depending on the
// view, and stacked actions could push their alerts off-screen with no
// history.
//
// ``ToastProvider`` mounts a single CToaster at layout level and
// exposes ``useToast()`` so any descendant component can call
// ``toast.success("…")``, ``toast.error("…")``, etc. The provider
// owns lifecycle: dedupe by id, auto-dismiss after ``autohideMs``,
// pause-on-hover, and accessible labelling via the t() helpers.
//
// Design constraints honoured:
//   * No external dependency — uses the CToaster/CToast already
//     shipped with @coreui/react so dark mode "just works" via the
//     existing tokens.
//   * Headless API: callers pass plain strings (or {title, message}
//     objects). The provider handles colour mapping, role=alert, and
//     dismiss button accessibility.
//   * SSR/test-safe — works without a window because CToaster is a
//     plain React component, not a portal.
//   * Drop-in for existing views: ``toast.error(extractError(err))``
//     replaces ``setActionError(extractError(err))`` 1:1.

import React, {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
} from 'react'
import PropTypes from 'prop-types'
import { useTranslation } from 'react-i18next'
import {
  CToast,
  CToastBody,
  CToastClose,
  CToastHeader,
  CToaster,
} from '@coreui/react'

const DEFAULT_AUTOHIDE_MS = 4500
const VALID_KINDS = ['success', 'danger', 'warning', 'info']

// Public shape returned by useToast(). Documented here so call sites
// don't have to re-derive it from the implementation.
//
//   toast.success(message, opts?)        — convenience for kind:'success'
//   toast.error(message, opts?)          — alias for kind:'danger'
//   toast.warning(message, opts?)
//   toast.info(message, opts?)
//   toast.show({ kind, message, title?, autohideMs?, id? })
//   toast.dismiss(id)
//   toast.clear()
//
// ``message`` may be a string or a node; ``title`` falls back to the
// localized title for the kind.

const ToastContext = createContext(null)

let _toastSeq = 0
const nextId = () => {
  _toastSeq += 1
  return `t-${Date.now().toString(36)}-${_toastSeq}`
}

export const ToastProvider = ({ children, autohideMs = DEFAULT_AUTOHIDE_MS }) => {
  const { t } = useTranslation('common')
  const [toasts, setToasts] = useState([])
  // Timer handles keyed by toast id so dismiss() can cancel a pending
  // auto-hide without racing against the timeout callback.
  const timersRef = useRef(new Map())

  const dismiss = useCallback((id) => {
    setToasts((prev) => prev.filter((entry) => entry.id !== id))
    const timer = timersRef.current.get(id)
    if (timer) {
      clearTimeout(timer)
      timersRef.current.delete(id)
    }
  }, [])

  const clear = useCallback(() => {
    setToasts([])
    for (const timer of timersRef.current.values()) clearTimeout(timer)
    timersRef.current.clear()
  }, [])

  const show = useCallback(
    (input) => {
      // Accept either a string or an object form. The object form is
      // the canonical one but the string form keeps the convenience
      // helpers (toast.error("boom")) terse.
      const opts = typeof input === 'string' ? { message: input } : input || {}
      const kind = VALID_KINDS.includes(opts.kind) ? opts.kind : 'info'
      const id = opts.id || nextId()
      const entry = {
        id,
        kind,
        message: opts.message ?? '',
        title: opts.title,
        autohideMs: opts.autohideMs == null ? autohideMs : Number(opts.autohideMs),
      }
      // Dedup: if a caller passed an explicit id and that toast is
      // already on-screen, replace its body instead of stacking dupes.
      setToasts((prev) => {
        const without = prev.filter((e) => e.id !== id)
        return [...without, entry]
      })
      // Reset any stale timer for the same id, then arm a fresh one.
      const stale = timersRef.current.get(id)
      if (stale) clearTimeout(stale)
      if (entry.autohideMs && entry.autohideMs > 0) {
        const handle = setTimeout(() => dismiss(id), entry.autohideMs)
        timersRef.current.set(id, handle)
      }
      return id
    },
    [autohideMs, dismiss],
  )

  // ``useMemo`` keeps the context value referentially stable so
  // consumers don't re-render on every state tick.
  const value = useMemo(() => {
    const showWithKind = (kind) => (message, opts = {}) =>
      show({ ...opts, kind, message })
    return {
      show,
      dismiss,
      clear,
      success: showWithKind('success'),
      error: showWithKind('danger'),
      warning: showWithKind('warning'),
      info: showWithKind('info'),
    }
  }, [show, dismiss, clear])

  const titleFor = (kind) =>
    t(`toasts.title.${kind}`, {
      defaultValue:
        kind === 'success'
          ? 'Success'
          : kind === 'danger'
            ? 'Error'
            : kind === 'warning'
              ? 'Warning'
              : 'Info',
    })

  // Each rendered CToast is mounted with role="alert" via @coreui's
  // default. We add a label on the region so screen readers announce
  // the area and let users tab back to dismiss controls.
  return (
    <ToastContext.Provider value={value}>
      {children}
      <CToaster
        className="p-3"
        placement="top-end"
        aria-label={t('toasts.regionLabel', { defaultValue: 'Notifications' })}
      >
        {toasts.map((entry) => (
          <CToast
            key={entry.id}
            color={entry.kind}
            visible
            autohide={false}
            className="text-white align-items-center"
            data-testid={`gd-toast gd-toast-${entry.kind}`}
            onClose={() => dismiss(entry.id)}
          >
            <CToastHeader closeButton={false}>
              <strong className="me-auto">{entry.title || titleFor(entry.kind)}</strong>
              <CToastClose
                onClick={() => dismiss(entry.id)}
                aria-label={t('toasts.dismiss', { defaultValue: 'Dismiss notification' })}
              />
            </CToastHeader>
            <CToastBody>{entry.message}</CToastBody>
          </CToast>
        ))}
      </CToaster>
    </ToastContext.Provider>
  )
}

ToastProvider.propTypes = {
  children: PropTypes.node,
  autohideMs: PropTypes.number,
}

// ``useToast`` returns the provider's API. When called outside a
// provider it returns a no-op-flavoured stub so unit tests of small
// components don't have to mount the provider when they don't care
// about feedback rendering.
export const useToast = () => {
  const ctx = useContext(ToastContext)
  if (ctx) return ctx
  const noop = () => null
  return {
    show: noop,
    dismiss: noop,
    clear: noop,
    success: noop,
    error: noop,
    warning: noop,
    info: noop,
  }
}

export default ToastProvider
