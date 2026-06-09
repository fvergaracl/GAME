// Create / edit a Task within a game.
//
// Same react-hook-form + CForm shell as GameFormModal, shaping the two modes:
//
//   • Create (POST /games/{id}/tasks): externalTaskId (req), strategyId
//     (opt - empty inherits the game's strategy) and params {key,value}.
//
//   • Edit (PATCH /games/{id}/tasks/{taskId}): PatchTask accepts
//     { strategyId, status, params }. externalTaskId stays immutable (shown
//     read-only); strategy, status and params are all editable. status is
//     seeded from the row's current value; params are synced server-side
//     (rows with an id update in place, new rows are created, removed rows
//     are deleted) so the editor grid is the desired full set. Each field is
//     only sent when it actually changed, so editing one never resets another.
//
// The task row we get from the list already carries everything edit needs
// (id, externalTaskId, strategy.id, status, taskParams), so edit never refetches.

import React, { useEffect, useMemo, useState } from 'react'
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
  CFormSelect,
  CFormText,
  CModal,
  CModalBody,
  CModalFooter,
  CModalHeader,
  CModalTitle,
  CSpinner,
} from '@coreui/react'

import { createTask, listBuiltInStrategies, listCustomStrategies, updateTask } from '../../../api'
import { extractError } from '../../../utils/errors'
import { useToast } from '../../../components/Toast'
import ParamsEditor from '../../../components/ParamsEditor'
import useUnsavedGuard from '../../../components/useUnsavedGuard'

// Same slug rule the Game form enforces (backend ``is_valid_slug``).
const SLUG_PATTERN = /^[a-zA-Z0-9_-]{3,60}$/

// Task status is a free string server-side (default "open"); these are the
// two lifecycle states worth surfacing in the UI.
const STATUS_OPTIONS = ['open', 'closed']

// Status picklist for edit mode: the two known states, plus the task's own
// current status if it's some other free-string value, so an edit never
// drops an unexpected status off the list.
const buildStatusOptions = (currentValue) => {
  const options = STATUS_OPTIONS.slice()
  if (currentValue && !options.includes(currentValue)) options.push(currentValue)
  return options
}

// See GameFormModal.coerceValue - re-narrow obvious numbers/booleans so a
// "10" param stays numeric instead of becoming the string "10".
const coerceValue = (raw) => {
  if (typeof raw !== 'string') return raw
  const s = raw.trim()
  if (s === '') return ''
  if (s === 'true') return true
  if (s === 'false') return false
  if (/^-?\d+$/.test(s)) return Number(s)
  if (/^-?\d*\.\d+$/.test(s)) return Number(s)
  return raw
}

// Build the strategy picklist: an "inherit from game" sentinel (empty value)
// on top, then built-ins, then published customs (as ``custom:<id>``). The
// task's current strategy is preserved even if it's archived/unlisted so an
// edit never silently reassigns it.
const buildStrategyOptions = (builtIns, customs, currentValue, inheritLabel) => {
  const options = [{ value: '', label: inheritLabel }]
  const seen = new Set([''])
  for (const row of builtIns || []) {
    if (!row?.id || seen.has(row.id)) continue
    options.push({ value: row.id, label: row.name || row.id })
    seen.add(row.id)
  }
  for (const row of customs || []) {
    if (!row?.id) continue
    const value = `custom:${row.id}`
    if (seen.has(value)) continue
    options.push({ value, label: `${row.name} v${row.version}` })
    seen.add(value)
  }
  if (currentValue && !seen.has(currentValue)) {
    options.push({ value: currentValue, label: currentValue })
  }
  return options
}

const TaskFormModal = ({ visible, mode, gameId, task, onClose, onSaved }) => {
  const { t } = useTranslation('management')
  const toast = useToast()

  const isEdit = mode === 'edit'

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting, isDirty },
  } = useForm({ defaultValues: { externalTaskId: '', strategyId: '', status: '' } })

  const [params, setParams] = useState([])
  // ParamsEditor (create mode only) lives outside react-hook-form; track its
  // edits separately so the unsaved-changes guard sees them. The load effect
  // re-seeds params via setParams directly, so it never trips this flag.
  const [paramsDirty, setParamsDirty] = useState(false)
  const handleParamsChange = (next) => {
    setParamsDirty(true)
    setParams(next)
  }
  const [strategyOptions, setStrategyOptions] = useState([])
  const [loadingDetail, setLoadingDetail] = useState(false)
  const [formError, setFormError] = useState(null)

  // Current strategy/status of the task being edited, so submit can tell
  // whether the admin actually changed each one (and skip no-op fields).
  const currentStrategyId = isEdit ? task?.strategy?.id || task?.strategyId || '' : ''
  const currentStatus = isEdit ? task?.status || '' : ''
  // Params the task currently has - used to seed the editor in edit mode.
  const existingParams = isEdit ? task?.taskParams || task?.params || [] : []

  const inheritLabel = t('tasks.form.inheritGame')
  const statusOptions = buildStatusOptions(currentStatus)

  // On open: fetch the strategy picklist (built-ins + published customs) and
  // seed the form. Strategy-list failures degrade gracefully to just the
  // "inherit" + current options.
  useEffect(() => {
    if (!visible) return undefined
    let cancelled = false
    setFormError(null)
    setParamsDirty(false)
    setLoadingDetail(true)

    Promise.all([
      listBuiltInStrategies().catch(() => []),
      listCustomStrategies({ status: 'PUBLISHED' }).catch(() => []),
    ])
      .then(([builtIns, customs]) => {
        if (cancelled) return
        setStrategyOptions(buildStrategyOptions(builtIns, customs, currentStrategyId, inheritLabel))
        if (isEdit) {
          reset({
            externalTaskId: task?.externalTaskId || '',
            strategyId: currentStrategyId,
            status: currentStatus,
          })
          // Seed the editor with the task's params. Keep each row's id so the
          // PATCH updates in place (vs. deleting + recreating); stringify the
          // value since the list endpoint may return it already coerced.
          setParams(
            existingParams.map((p) => ({
              id: p.id,
              key: p.key ?? '',
              value: p.value === null || p.value === undefined ? '' : String(p.value),
            })),
          )
        } else {
          reset({ externalTaskId: '', strategyId: '', status: '' })
          setParams([])
        }
      })
      .catch((err) => {
        if (!cancelled) setFormError(extractError(err, t('common.loadError')))
      })
      .finally(() => {
        if (!cancelled) setLoadingDetail(false)
      })

    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visible, isEdit, task, gameId])

  const cleanedParams = useMemo(
    () => params.map((p) => ({ ...p, key: (p.key || '').trim() })).filter((p) => p.key.length > 0),
    [params],
  )

  const onSubmit = async (values) => {
    setFormError(null)
    try {
      if (isEdit) {
        // PatchTask takes { strategyId, status, params }. Send each field only
        // when it actually changed so editing one never resets another.
        const payload = {}
        if (values.strategyId !== currentStrategyId) {
          payload.strategyId = values.strategyId || 'default'
        }
        if (values.status && values.status !== currentStatus) {
          payload.status = values.status
        }
        if (paramsDirty) {
          // The editor grid is the desired full set; preserve ids so existing
          // rows update in place and dropped rows get deleted server-side.
          payload.params = cleanedParams.map((p) => {
            const entry = { key: p.key, value: coerceValue(p.value) }
            if (p.id) entry.id = p.id
            return entry
          })
        }
        if (Object.keys(payload).length === 0) {
          // Nothing changed - close without hitting the API (PATCH 409s on an
          // empty patch anyway).
          onClose?.()
          return
        }
        await updateTask(gameId, task.id, payload)
        toast.success(t('feedback.taskUpdated'))
      } else {
        const payload = { externalTaskId: values.externalTaskId.trim() }
        if (values.strategyId) payload.strategyId = values.strategyId
        const createParams = cleanedParams.map((p) => ({
          key: p.key,
          value: coerceValue(p.value),
        }))
        if (createParams.length) payload.params = createParams
        await createTask(gameId, payload)
        toast.success(t('feedback.taskCreated'))
      }
      onSaved?.()
      onClose?.()
    } catch (err) {
      const msg = extractError(err, t('common.loadError'))
      setFormError(msg)
      toast.error(msg)
    }
  }

  const busy = isSubmitting || loadingDetail

  const handleClose = useUnsavedGuard({
    dirty: isDirty || paramsDirty,
    blocked: busy,
    onClose,
  })

  return (
    <CModal visible={visible} onClose={handleClose} size="lg" backdrop="static">
      <CModalHeader closeButton={!busy}>
        <CModalTitle>{isEdit ? t('tasks.editTitle') : t('tasks.createTitle')}</CModalTitle>
      </CModalHeader>
      <CForm onSubmit={handleSubmit(onSubmit)}>
        <CModalBody>
          {formError && <CAlert color="danger">{formError}</CAlert>}

          {loadingDetail ? (
            <div className="d-flex align-items-center gap-2 py-4 justify-content-center text-medium-emphasis">
              <CSpinner size="sm" /> {t('common:loading')}
            </div>
          ) : (
            <>
              <div className="mb-3">
                <CFormLabel htmlFor="task-externalTaskId">
                  {t('tasks.form.externalTaskId')}
                </CFormLabel>
                <CFormInput
                  id="task-externalTaskId"
                  type="text"
                  placeholder="task-login"
                  readOnly={isEdit}
                  disabled={isEdit}
                  invalid={!!errors.externalTaskId}
                  {...register('externalTaskId', {
                    required: isEdit ? false : t('common.required'),
                    pattern: isEdit
                      ? undefined
                      : {
                          value: SLUG_PATTERN,
                          message: t('tasks.form.externalTaskIdInvalid'),
                        },
                  })}
                />
                {errors.externalTaskId ? (
                  <CFormFeedback invalid>{errors.externalTaskId.message}</CFormFeedback>
                ) : (
                  <CFormText>
                    {isEdit
                      ? t('tasks.form.externalTaskIdReadonly')
                      : t('tasks.form.externalTaskIdHelp')}
                  </CFormText>
                )}
              </div>

              <div className="mb-3">
                <CFormLabel htmlFor="task-strategyId">{t('tasks.form.strategyId')}</CFormLabel>
                <CFormSelect id="task-strategyId" {...register('strategyId')}>
                  {strategyOptions.map((opt) => (
                    <option key={opt.value || '__inherit__'} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </CFormSelect>
                <CFormText>{t('tasks.form.strategyHelp')}</CFormText>
              </div>

              {isEdit && (
                <div className="mb-3">
                  <CFormLabel htmlFor="task-status">{t('tasks.form.status')}</CFormLabel>
                  <CFormSelect id="task-status" {...register('status')}>
                    {/* Fallback "keep current" only when the row has no known
                        status, so we never silently flip it to "open". */}
                    {!currentStatus && (
                      <option value="">{t('tasks.form.statusKeep')}</option>
                    )}
                    {statusOptions.map((s) => (
                      <option key={s} value={s}>
                        {t(`tasks.statusOptions.${s}`, { defaultValue: s })}
                      </option>
                    ))}
                  </CFormSelect>
                </div>
              )}

              <div className="mb-2">
                <CFormLabel>{t('tasks.form.params')}</CFormLabel>
                <ParamsEditor
                  value={params}
                  onChange={handleParamsChange}
                  disabled={isSubmitting}
                />
                {isEdit && <CFormText>{t('tasks.form.paramsEditNote')}</CFormText>}
              </div>
            </>
          )}
        </CModalBody>
        <CModalFooter>
          <CButton color="secondary" variant="outline" onClick={handleClose} disabled={busy}>
            {t('actions.cancel')}
          </CButton>
          <CButton color="primary" type="submit" disabled={busy}>
            {isSubmitting && <CSpinner size="sm" className="me-2" />}
            {isSubmitting ? t('actions.saving') : t('actions.save')}
          </CButton>
        </CModalFooter>
      </CForm>
    </CModal>
  )
}

TaskFormModal.propTypes = {
  visible: PropTypes.bool.isRequired,
  mode: PropTypes.oneOf(['create', 'edit']).isRequired,
  gameId: PropTypes.string.isRequired,
  task: PropTypes.object,
  onClose: PropTypes.func.isRequired,
  onSaved: PropTypes.func,
}

export default TaskFormModal
