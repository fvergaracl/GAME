// Sprint 0 (CRUD management) - repeatable {key, value} params editor.
//
// Both the Game and Task forms expose the same "strategy params" grid: a
// list of key/value pairs the admin can grow or trim. Rather than build it
// twice, this controlled component owns the add/remove/edit row mechanics
// and hands the parent a clean array back through onChange.
//
// Controlled by design so it slots into react-hook-form via a Controller:
// the parent holds the source of truth (``value``) and re-renders us with
// the next array. Existing params loaded from the backend keep their ``id``
// (the PATCH game-params path needs it); brand-new rows get a transient
// ``_rid`` purely so React has a stable key while the row is unsaved.

import React from 'react'
import PropTypes from 'prop-types'
import { useTranslation } from 'react-i18next'
import { CButton, CCol, CFormInput, CRow } from '@coreui/react'
import CIcon from '@coreui/icons-react'
import { cilPlus, cilTrash } from '@coreui/icons'

let _ridSeq = 0
const nextRid = () => {
  _ridSeq += 1
  return `p-${_ridSeq}`
}

const ParamsEditor = ({
  value = [],
  onChange,
  disabled = false,
  keyPlaceholder,
  valuePlaceholder,
}) => {
  const { t } = useTranslation('management')
  const rows = Array.isArray(value) ? value : []

  const emit = (next) => onChange?.(next)

  const updateField = (idx, field, fieldValue) => {
    emit(rows.map((row, i) => (i === idx ? { ...row, [field]: fieldValue } : row)))
  }

  const addRow = () => emit([...rows, { key: '', value: '', _rid: nextRid() }])

  const removeRow = (idx) => emit(rows.filter((_, i) => i !== idx))

  const resolvedKeyPh =
    keyPlaceholder || t('params.keyPlaceholder', { defaultValue: 'Key' })
  const resolvedValuePh =
    valuePlaceholder || t('params.valuePlaceholder', { defaultValue: 'Value' })

  return (
    <div>
      {rows.length === 0 && (
        <p className="text-medium-emphasis small mb-2">
          {t('params.empty', { defaultValue: 'No parameters yet.' })}
        </p>
      )}

      {rows.map((row, idx) => (
        <CRow className="g-2 mb-2 align-items-center" key={row.id || row._rid || idx}>
          <CCol xs={5}>
            <CFormInput
              type="text"
              value={row.key ?? ''}
              placeholder={resolvedKeyPh}
              disabled={disabled}
              aria-label={resolvedKeyPh}
              onChange={(e) => updateField(idx, 'key', e.target.value)}
            />
          </CCol>
          <CCol xs={5}>
            <CFormInput
              type="text"
              value={row.value ?? ''}
              placeholder={resolvedValuePh}
              disabled={disabled}
              aria-label={resolvedValuePh}
              onChange={(e) => updateField(idx, 'value', e.target.value)}
            />
          </CCol>
          <CCol xs={2}>
            <CButton
              color="danger"
              variant="outline"
              className="w-100"
              disabled={disabled}
              aria-label={t('params.removeRow', { defaultValue: 'Remove parameter' })}
              onClick={() => removeRow(idx)}
            >
              <CIcon icon={cilTrash} />
            </CButton>
          </CCol>
        </CRow>
      ))}

      <CButton
        color="secondary"
        variant="outline"
        size="sm"
        disabled={disabled}
        onClick={addRow}
      >
        <CIcon icon={cilPlus} className="me-1" />
        {t('params.addRow', { defaultValue: 'Add parameter' })}
      </CButton>
    </div>
  )
}

ParamsEditor.propTypes = {
  value: PropTypes.arrayOf(PropTypes.object),
  onChange: PropTypes.func,
  disabled: PropTypes.bool,
  keyPlaceholder: PropTypes.string,
  valuePlaceholder: PropTypes.string,
}

export default ParamsEditor
