// Sprint 3 (CRUD management) — bulk-create tasks in a game.
//
// POST /games/{gameId}/tasks/bulk takes a list of task payloads and returns a
// PARTITIONED result: { succesfully_created, failed_to_create:[{task,error}] }.
// That partial-success shape is the whole point of this modal — the admin
// pastes one externalTaskId per line, optionally pins a shared strategy, and
// we report exactly which ids landed and which collided, then re-seed the box
// with only the failures so a retry is one edit away.

import React, { useEffect, useMemo, useState } from 'react'
import PropTypes from 'prop-types'
import { useTranslation } from 'react-i18next'
import {
  CAlert,
  CButton,
  CForm,
  CFormLabel,
  CFormSelect,
  CFormText,
  CFormTextarea,
  CModal,
  CModalBody,
  CModalFooter,
  CModalHeader,
  CModalTitle,
  CSpinner,
} from '@coreui/react'

import { bulkCreateTasks, listBuiltInStrategies, listCustomStrategies } from '../../../api'
import { extractError } from '../../../utils/errors'
import { useToast } from '../../../components/Toast'

const SLUG_PATTERN = /^[a-zA-Z0-9_-]{3,60}$/

// Split a textarea blob into trimmed, de-duplicated, non-empty lines.
const parseIds = (text) => {
  const seen = new Set()
  const ids = []
  for (const raw of (text || '').split('\n')) {
    const id = raw.trim()
    if (!id || seen.has(id)) continue
    seen.add(id)
    ids.push(id)
  }
  return ids
}

const buildStrategyOptions = (builtIns, customs, inheritLabel) => {
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
  return options
}

const TaskBulkModal = ({ visible, gameId, onClose, onCreated }) => {
  const { t } = useTranslation('management')
  const toast = useToast()

  const [text, setText] = useState('')
  const [strategyId, setStrategyId] = useState('')
  const [strategyOptions, setStrategyOptions] = useState([])
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState(null)
  // Failures from the last submit: [{ externalTaskId, error }].
  const [failures, setFailures] = useState([])

  const inheritLabel = t('tasks.form.inheritGame')

  useEffect(() => {
    if (!visible) return undefined
    let cancelled = false
    setText('')
    setStrategyId('')
    setFormError(null)
    setFailures([])
    Promise.all([
      listBuiltInStrategies().catch(() => []),
      listCustomStrategies({ status: 'PUBLISHED' }).catch(() => []),
    ]).then(([builtIns, customs]) => {
      if (!cancelled) setStrategyOptions(buildStrategyOptions(builtIns, customs, inheritLabel))
    })
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visible, gameId])

  const ids = useMemo(() => parseIds(text), [text])
  const invalidIds = useMemo(() => ids.filter((id) => !SLUG_PATTERN.test(id)), [ids])
  const canSubmit = ids.length > 0 && invalidIds.length === 0 && !submitting

  const onSubmit = async (e) => {
    e.preventDefault()
    if (!canSubmit) return
    setFormError(null)
    setFailures([])
    setSubmitting(true)
    try {
      const tasks = ids.map((externalTaskId) =>
        strategyId ? { externalTaskId, strategyId } : { externalTaskId },
      )
      const result = await bulkCreateTasks(gameId, tasks)
      const created = result?.succesfully_created || []
      const failed = result?.failed_to_create || []
      // Refresh the table whenever at least one task landed.
      if (created.length > 0) onCreated?.()
      toast.success(
        t('feedback.tasksBulkCreated', { count: created.length, failed: failed.length }),
      )
      if (failed.length === 0) {
        onClose?.()
      } else {
        // Keep the modal open, surface the errors, and re-seed the box with
        // only the ids that failed so the admin can fix and retry.
        const failedRows = failed.map((f) => ({
          externalTaskId: f?.task?.externalTaskId || '',
          error: f?.error || '',
        }))
        setFailures(failedRows)
        setText(failedRows.map((f) => f.externalTaskId).join('\n'))
      }
    } catch (err) {
      setFormError(extractError(err, t('common.loadError')))
    } finally {
      setSubmitting(false)
    }
  }

  const handleClose = () => {
    if (submitting) return
    onClose?.()
  }

  return (
    <CModal visible={visible} onClose={handleClose} size="lg" backdrop="static">
      <CModalHeader closeButton={!submitting}>
        <CModalTitle>{t('tasks.bulk.title')}</CModalTitle>
      </CModalHeader>
      <CForm onSubmit={onSubmit}>
        <CModalBody>
          {formError && <CAlert color="danger">{formError}</CAlert>}

          {failures.length > 0 && (
            <CAlert color="warning">
              <p className="mb-1">{t('tasks.bulk.someFailed', { count: failures.length })}</p>
              <ul className="mb-0 small">
                {failures.map((f, i) => (
                  <li key={`${f.externalTaskId}-${i}`}>
                    <code>{f.externalTaskId}</code>
                    {f.error ? ` — ${f.error}` : ''}
                  </li>
                ))}
              </ul>
            </CAlert>
          )}

          <div className="mb-3">
            <CFormLabel htmlFor="bulk-strategyId">{t('tasks.form.strategyId')}</CFormLabel>
            <CFormSelect
              id="bulk-strategyId"
              value={strategyId}
              disabled={submitting}
              onChange={(e) => setStrategyId(e.target.value)}
            >
              {strategyOptions.map((opt) => (
                <option key={opt.value || '__inherit__'} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </CFormSelect>
            <CFormText>{t('tasks.bulk.strategyHelp')}</CFormText>
          </div>

          <div className="mb-2">
            <CFormLabel htmlFor="bulk-ids">{t('tasks.bulk.label')}</CFormLabel>
            <CFormTextarea
              id="bulk-ids"
              rows={8}
              placeholder={t('tasks.bulk.placeholder')}
              value={text}
              disabled={submitting}
              onChange={(e) => setText(e.target.value)}
            />
            <CFormText>{t('tasks.bulk.help')}</CFormText>
          </div>

          {ids.length > 0 && (
            <p className="small mb-0">
              {invalidIds.length > 0 ? (
                <span className="text-danger">
                  {t('tasks.bulk.invalid', {
                    count: invalidIds.length,
                    ids: invalidIds.join(', '),
                  })}
                </span>
              ) : (
                <span className="text-medium-emphasis">
                  {t('tasks.bulk.ready', { count: ids.length })}
                </span>
              )}
            </p>
          )}
        </CModalBody>
        <CModalFooter>
          <CButton color="secondary" variant="outline" onClick={handleClose} disabled={submitting}>
            {t('actions.cancel')}
          </CButton>
          <CButton color="primary" type="submit" disabled={!canSubmit}>
            {submitting && <CSpinner size="sm" className="me-2" />}
            {t('tasks.bulk.confirm', { count: ids.length })}
          </CButton>
        </CModalFooter>
      </CForm>
    </CModal>
  )
}

TaskBulkModal.propTypes = {
  visible: PropTypes.bool,
  gameId: PropTypes.string,
  onClose: PropTypes.func,
  onCreated: PropTypes.func,
}

export default TaskBulkModal
