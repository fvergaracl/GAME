// Sprint 3 (CRUD management) — duplicate a Task within the same game.
//
// Mirror of GameDuplicateModal: the backend POST
// /games/{gameId}/tasks/{taskId}/duplicate deep-copies the source task's
// strategy + params onto a new externalTaskId (starting in the default
// "open" status). This modal only collects that new id, with the same slug
// validation and a "copy-of-…" pre-fill so the common case is one click.
//
// taskId here is the INTERNAL uuid (task.id) — the duplicate route is keyed
// on it, not on the external id. Uniqueness can't be checked client-side, so
// a collision returns 409 and is surfaced inline via extractError.

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

import { duplicateTask } from '../../../api'
import { extractError } from '../../../utils/errors'
import { useToast } from '../../../components/Toast'
import useUnsavedGuard from '../../../components/useUnsavedGuard'

const SLUG_PATTERN = /^[a-zA-Z0-9_-]{3,60}$/

const suggestId = (sourceExternalTaskId) => `copy-of-${sourceExternalTaskId || ''}`.slice(0, 60)

const TaskDuplicateModal = ({ visible, gameId, task, onClose, onDuplicated }) => {
  const { t } = useTranslation('management')
  const toast = useToast()

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting, isDirty },
  } = useForm({ defaultValues: { externalTaskId: '' } })

  const [formError, setFormError] = useState(null)

  const taskId = task?.id != null ? String(task.id) : null
  const sourceExternalTaskId = task?.externalTaskId || ''

  useEffect(() => {
    if (!visible) return
    setFormError(null)
    reset({ externalTaskId: suggestId(sourceExternalTaskId) })
  }, [visible, sourceExternalTaskId, reset])

  const onSubmit = async (values) => {
    if (!taskId) return
    setFormError(null)
    try {
      await duplicateTask(gameId, taskId, { externalTaskId: values.externalTaskId.trim() })
      toast.success(t('feedback.taskDuplicated'))
      onDuplicated?.()
      onClose?.()
    } catch (err) {
      const msg = extractError(err, t('common.loadError'))
      setFormError(msg)
      toast.error(msg)
    }
  }

  const handleClose = useUnsavedGuard({ dirty: isDirty, blocked: isSubmitting, onClose })

  return (
    <CModal visible={visible} onClose={handleClose} backdrop="static">
      <CModalHeader closeButton={!isSubmitting}>
        <CModalTitle>{t('tasks.duplicate.title')}</CModalTitle>
      </CModalHeader>
      <CForm onSubmit={handleSubmit(onSubmit)}>
        <CModalBody>
          {formError && <CAlert color="danger">{formError}</CAlert>}

          <p className="text-medium-emphasis">
            {t('tasks.duplicate.message', { externalTaskId: sourceExternalTaskId })}
          </p>

          <div className="mb-2">
            <CFormLabel htmlFor="duplicate-externalTaskId">{t('tasks.duplicate.label')}</CFormLabel>
            <CFormInput
              id="duplicate-externalTaskId"
              type="text"
              placeholder={t('tasks.duplicate.placeholder')}
              invalid={!!errors.externalTaskId}
              {...register('externalTaskId', {
                required: t('common.required'),
                pattern: {
                  value: SLUG_PATTERN,
                  message: t('tasks.form.externalTaskIdInvalid'),
                },
              })}
            />
            {errors.externalTaskId ? (
              <CFormFeedback invalid>{errors.externalTaskId.message}</CFormFeedback>
            ) : (
              <CFormText>{t('tasks.form.externalTaskIdHelp')}</CFormText>
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
            {t('tasks.duplicate.confirm')}
          </CButton>
        </CModalFooter>
      </CForm>
    </CModal>
  )
}

TaskDuplicateModal.propTypes = {
  visible: PropTypes.bool,
  gameId: PropTypes.string,
  task: PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    externalTaskId: PropTypes.string,
  }),
  onClose: PropTypes.func,
  onDuplicated: PropTypes.func,
}

export default TaskDuplicateModal
