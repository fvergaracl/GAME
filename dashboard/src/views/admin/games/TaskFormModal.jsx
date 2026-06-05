// Sprint 3 (CRUD management) — create / edit a Task within a game.
//
// Same react-hook-form + CForm shell as GameFormModal, but the task backend
// is more constrained, and those constraints shape the two modes:
//
//   • Create (POST /games/{id}/tasks): externalTaskId (req), strategyId
//     (opt — empty inherits the game's strategy) and params {key,value}.
//
//   • Edit (PATCH /games/{id}/tasks/{taskId}): the backend's PatchTask only
//     accepts { strategyId, status }. externalTaskId and params CANNOT be
//     changed here, so we render them read-only with a note. status is never
//     returned by any GET, so its select defaults to "keep current" and is
//     only sent when the admin picks a concrete value — otherwise editing the
//     strategy would silently reset a task's status.
//
// The task row we get from the list already carries everything edit needs
// (id, externalTaskId, strategy.id, taskParams), so edit mode never refetches.

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
// two lifecycle states worth surfacing. The empty value is the "keep current"
// sentinel — selecting it omits status from the PATCH entirely.
const STATUS_OPTIONS = ['open', 'closed']

// See GameFormModal.coerceValue — re-narrow obvious numbers/booleans so a
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

  // The current strategy of the task being edited, so submit can tell whether
  // the admin actually changed it (and skip a no-op PATCH otherwise).
  const currentStrategyId = isEdit ? task?.strategy?.id || task?.strategyId || '' : ''
  // Read-only params shown in edit mode (PATCH can't mutate them).
  const existingParams = isEdit ? task?.taskParams || task?.params || [] : []

  const inheritLabel = t('tasks.form.inheritGame')

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
            status: '',
          })
          setParams([])
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
        // PatchTask only takes { strategyId, status }. Send strategyId only
        // when changed, status only when a concrete value was chosen.
        const payload = {}
        if (values.strategyId !== currentStrategyId) {
          payload.strategyId = values.strategyId || 'default'
        }
        if (values.status) payload.status = values.status
        if (Object.keys(payload).length === 0) {
          // Nothing changed — close without hitting the API (PATCH 400s on an
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
                    <option value="">{t('tasks.form.statusKeep')}</option>
                    {STATUS_OPTIONS.map((s) => (
                      <option key={s} value={s}>
                        {t(`tasks.statusOptions.${s}`, { defaultValue: s })}
                      </option>
                    ))}
                  </CFormSelect>
                </div>
              )}

              <div className="mb-2">
                <CFormLabel>{t('tasks.form.params')}</CFormLabel>
                {isEdit ? (
                  <>
                    {existingParams.length > 0 ? (
                      <ul className="list-unstyled mb-1 small">
                        {existingParams.map((p, i) => (
                          <li key={p.id || `${p.key}-${i}`}>
                            <code>{p.key}</code>
                            {': '}
                            <span className="text-medium-emphasis">{String(p.value)}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-medium-emphasis small mb-1">{t('params.empty')}</p>
                    )}
                    <CFormText>{t('tasks.form.paramsEditNote')}</CFormText>
                  </>
                ) : (
                  <ParamsEditor value={params} onChange={handleParamsChange} disabled={isSubmitting} />
                )}
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
