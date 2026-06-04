// Sprint 2 (CRUD management) — duplicate a Game (deep copy).
//
// The backend POST /games/{id}/duplicate does the heavy lifting: it clones
// the game's platform/strategy/params and every task with its own params
// under a new externalGameId. All this modal needs is to collect that new id.
//
// Why a dedicated modal instead of ConfirmDialog: duplicating asks for input
// (the new externalGameId) with the same slug validation create/edit use, so
// it follows the react-hook-form + CFormFeedback pattern from GameFormModal
// rather than the input-less ConfirmDialog. The field is pre-seeded with a
// "copy-of-…" suggestion so the common case is one click.
//
// Uniqueness can't be checked client-side, so a collision comes back as a
// 409 from the server; we surface it inline via extractError and leave the
// modal open so the admin can pick another id without re-typing everything.

import React, { useEffect, useState } from 'react'
import PropTypes from 'prop-types'
import { useForm } from 'react-hook-form'
import { useTranslation } from 'react-i18next'
import {
  CAlert,
  CButton,
  CForm,
  CFormFeedback,
  CFormInput,
  CFormLabel,
  CFormText,
  CModal,
  CModalBody,
  CModalFooter,
  CModalHeader,
  CModalTitle,
  CSpinner,
} from '@coreui/react'

import { duplicateGame } from '../../../api'
import { extractError } from '../../../utils/errors'
import { useToast } from '../../../components/Toast'

// Slug rule mirrors the backend ``is_valid_slug``: ^[a-z0-9_-]{3,60}$
// (case-insensitive). Same constraint GameFormModal enforces on create/edit.
const SLUG_PATTERN = /^[a-zA-Z0-9_-]{3,60}$/

// Pre-fill suggestion: "copy-of-<source>", capped to the 60-char slug limit
// so a long source id still yields a valid default.
const suggestId = (sourceExternalGameId) =>
  `copy-of-${sourceExternalGameId || ''}`.slice(0, 60)

const GameDuplicateModal = ({ visible, game, onClose, onDuplicated }) => {
  const { t } = useTranslation('management')
  const toast = useToast()

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm({ defaultValues: { externalGameId: '' } })

  const [formError, setFormError] = useState(null)

  const gameId = game?.gameId != null ? String(game.gameId) : null
  const sourceExternalGameId = game?.externalGameId || ''

  // Seed the suggestion each time the modal opens for a (possibly new) game.
  useEffect(() => {
    if (!visible) return
    setFormError(null)
    reset({ externalGameId: suggestId(sourceExternalGameId) })
  }, [visible, sourceExternalGameId, reset])

  const onSubmit = async (values) => {
    if (!gameId) return
    setFormError(null)
    try {
      await duplicateGame(gameId, { externalGameId: values.externalGameId.trim() })
      toast.success(t('feedback.gameDuplicated'))
      onDuplicated?.()
      onClose?.()
    } catch (err) {
      const msg = extractError(err, t('common.loadError'))
      setFormError(msg)
      toast.error(msg)
    }
  }

  const handleClose = () => {
    if (isSubmitting) return
    onClose?.()
  }

  return (
    <CModal visible={visible} onClose={handleClose} backdrop="static">
      <CModalHeader closeButton={!isSubmitting}>
        <CModalTitle>{t('games.duplicate.title')}</CModalTitle>
      </CModalHeader>
      <CForm onSubmit={handleSubmit(onSubmit)}>
        <CModalBody>
          {formError && <CAlert color="danger">{formError}</CAlert>}

          <p className="text-medium-emphasis">
            {t('games.duplicate.message', { externalGameId: sourceExternalGameId })}
          </p>

          <div className="mb-2">
            <CFormLabel htmlFor="duplicate-externalGameId">
              {t('games.duplicate.label')}
            </CFormLabel>
            <CFormInput
              id="duplicate-externalGameId"
              type="text"
              placeholder={t('games.duplicate.placeholder')}
              invalid={!!errors.externalGameId}
              {...register('externalGameId', {
                required: t('common.required'),
                pattern: {
                  value: SLUG_PATTERN,
                  message: t('games.form.externalGameIdInvalid'),
                },
              })}
            />
            {errors.externalGameId ? (
              <CFormFeedback invalid>{errors.externalGameId.message}</CFormFeedback>
            ) : (
              <CFormText>{t('games.form.externalGameIdHelp')}</CFormText>
            )}
          </div>
        </CModalBody>
        <CModalFooter>
          <CButton
            color="secondary"
            variant="outline"
            onClick={handleClose}
            disabled={isSubmitting}
          >
            {t('actions.cancel')}
          </CButton>
          <CButton color="primary" type="submit" disabled={isSubmitting}>
            {isSubmitting && <CSpinner size="sm" className="me-2" />}
            {t('games.duplicate.confirm')}
          </CButton>
        </CModalFooter>
      </CForm>
    </CModal>
  )
}

GameDuplicateModal.propTypes = {
  visible: PropTypes.bool,
  game: PropTypes.shape({
    gameId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    externalGameId: PropTypes.string,
  }),
  onClose: PropTypes.func,
  onDuplicated: PropTypes.func,
}

export default GameDuplicateModal
