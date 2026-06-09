// Shared "discard unsaved changes?" guard.
//
// Every management form modal (game/task create-edit, duplicate, bulk) can
// be dismissed three ways: the header X, the Cancel button and the Esc key.
// All three should warn before throwing away typed-but-unsaved input instead
// of silently closing. This hook centralises that single decision so the
// five modals don't each re-implement it (and drift on the wording).
//
//   const handleClose = useUnsavedGuard({ dirty, blocked: busy, onClose })
//
// ``dirty``   - is there anything the user would lose by closing now?
// ``blocked`` - an in-flight request: swallow the close entirely so the
//               modal can't be dismissed mid-save and desync the UI.
// ``onClose`` - the real close callback, run only once we're clear to go.
//
// The prompt uses window.confirm: it's keyboard-operable and announced by
// screen readers, and avoids nesting a second CModal inside the form modal
// (which fights CoreUI's focus trap).

import { useCallback } from 'react'
import { useTranslation } from 'react-i18next'

export const useUnsavedGuard = ({ dirty, blocked = false, onClose }) => {
  const { t } = useTranslation('management')
  return useCallback(() => {
    if (blocked) return
    if (dirty && !window.confirm(t('common.unsavedChanges'))) return
    onClose?.()
  }, [dirty, blocked, onClose, t])
}

export default useUnsavedGuard
