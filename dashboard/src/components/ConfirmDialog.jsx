// Reusable confirmation modal.
//
// Lifts the inline confirm modal that StrategyLibraryView hand-rolled for
// publish/archive into a single component so every destructive or
// irreversible action (delete game/task, revoke API key, duplicate) gets
// the same look, the same busy handling, and the same a11y wiring instead
// of each view re-implementing a CModal + footer + spinner.
//
// Accessibility: CoreUI's CModal already traps focus and closes on Esc /
// backdrop. We add an aria-busy on the body while the action runs and a
// described-by link between the title and the message so screen readers
// announce both. The confirm button takes focus on open so keyboard users
// can Enter-to-confirm, except for destructive actions where we leave focus
// on Cancel to avoid an accidental Enter wiping data.

import React, { useEffect, useRef } from 'react'
import PropTypes from 'prop-types'
import { useTranslation } from 'react-i18next'
import {
  CButton,
  CModal,
  CModalBody,
  CModalFooter,
  CModalHeader,
  CModalTitle,
  CSpinner,
} from '@coreui/react'

const ConfirmDialog = ({
  visible,
  title,
  message,
  confirmLabel,
  cancelLabel,
  // Bootstrap colour for the confirm button. 'danger' also flips initial
  // focus to Cancel so Enter doesn't immediately run a destructive action.
  confirmColor = 'primary',
  busy = false,
  onConfirm,
  onCancel,
}) => {
  const { t } = useTranslation('management')
  const confirmRef = useRef(null)
  const cancelRef = useRef(null)

  const isDestructive = confirmColor === 'danger' || confirmColor === 'dark'

  useEffect(() => {
    if (!visible) return
    // Defer to the next tick so the modal node is mounted before we focus.
    const id = window.setTimeout(() => {
      const target = isDestructive ? cancelRef.current : confirmRef.current
      target?.focus()
    }, 0)
    return () => window.clearTimeout(id)
  }, [visible, isDestructive])

  const resolvedConfirm = confirmLabel || t('actions.confirm', { defaultValue: 'Confirm' })
  const resolvedCancel = cancelLabel || t('actions.cancel', { defaultValue: 'Cancel' })

  // Block the close handlers while busy so the user can't dismiss a modal
  // mid-request and desync the optimistic UI.
  const handleClose = () => {
    if (busy) return
    onCancel?.()
  }

  return (
    <CModal
      visible={visible}
      onClose={handleClose}
      aria-labelledby="confirm-dialog-title"
      aria-describedby="confirm-dialog-body"
    >
      <CModalHeader closeButton={!busy}>
        <CModalTitle id="confirm-dialog-title">{title}</CModalTitle>
      </CModalHeader>
      <CModalBody id="confirm-dialog-body" aria-busy={busy}>
        {message}
      </CModalBody>
      <CModalFooter>
        <CButton
          ref={cancelRef}
          color="secondary"
          variant="outline"
          onClick={handleClose}
          disabled={busy}
        >
          {resolvedCancel}
        </CButton>
        <CButton
          ref={confirmRef}
          color={confirmColor}
          onClick={onConfirm}
          disabled={busy}
        >
          {busy && <CSpinner size="sm" className="me-2" />}
          {resolvedConfirm}
        </CButton>
      </CModalFooter>
    </CModal>
  )
}

ConfirmDialog.propTypes = {
  visible: PropTypes.bool,
  title: PropTypes.node,
  message: PropTypes.node,
  confirmLabel: PropTypes.node,
  cancelLabel: PropTypes.node,
  confirmColor: PropTypes.string,
  busy: PropTypes.bool,
  onConfirm: PropTypes.func,
  onCancel: PropTypes.func,
}

export default ConfirmDialog
