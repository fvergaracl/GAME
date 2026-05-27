// Sprint 8: template picker modal.
//
// Fetches /v1/strategies/custom/templates on open and renders a grid of
// CCards. Selecting one fires ``onSelect(template)`` and closes the
// modal — the StrategyEditor handles the actual workspace loading so
// the modal stays render-only.

import React, { useEffect, useState } from 'react'
import PropTypes from 'prop-types'
import {
  CAlert,
  CBadge,
  CButton,
  CCard,
  CCardBody,
  CCardText,
  CCardTitle,
  CCol,
  CModal,
  CModalBody,
  CModalFooter,
  CModalHeader,
  CModalTitle,
  CRow,
  CSpinner,
} from '@coreui/react'

import { listStrategyTemplates } from '../../api'

const TemplatePickerModal = ({ visible, onClose, onSelect }) => {
  const [templates, setTemplates] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  // Re-fetch every time the modal opens — the list is small (~4 items)
  // and templates may have been edited between sessions. The trade-off
  // vs. caching is favoured by simplicity here.
  useEffect(() => {
    if (!visible) return
    let cancelled = false
    setIsLoading(true)
    setError(null)
    listStrategyTemplates()
      .then((rows) => {
        if (cancelled) return
        setTemplates(Array.isArray(rows) ? rows : [])
      })
      .catch((err) => {
        if (cancelled) return
        setError(
          err?.response?.data?.detail || err?.message || 'No se pudieron cargar las plantillas.',
        )
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [visible])

  return (
    <CModal visible={visible} onClose={onClose} size="lg">
      <CModalHeader>
        <CModalTitle>Elige una plantilla</CModalTitle>
      </CModalHeader>
      <CModalBody>
        {isLoading && (
          <div className="d-flex justify-content-center py-4">
            <CSpinner />
          </div>
        )}
        {error && <CAlert color="danger">{error}</CAlert>}
        {!isLoading && !error && templates.length === 0 && (
          <CAlert color="info">
            No hay plantillas disponibles. Pide al administrador que añada archivos en{' '}
            <code>app/engine/dsl_templates/user/</code>.
          </CAlert>
        )}
        <CRow>
          {templates.map((tpl) => (
            <CCol md={6} key={tpl.id} className="mb-3">
              <CCard className="h-100">
                <CCardBody className="d-flex flex-column">
                  <CCardTitle>
                    {tpl.name}{' '}
                    <CBadge color={tpl.type === 'DSL_EXTEND' ? 'warning' : 'info'} className="ms-2">
                      {tpl.type}
                    </CBadge>
                  </CCardTitle>
                  {tpl.parentStrategyId && (
                    <small className="text-medium-emphasis mb-2">
                      Extiende: <code>{tpl.parentStrategyId}</code>
                    </small>
                  )}
                  <CCardText className="flex-grow-1">
                    {tpl.description || 'Sin descripción.'}
                  </CCardText>
                  <CButton
                    color="primary"
                    onClick={() => {
                      onSelect(tpl)
                      onClose()
                    }}
                  >
                    Usar plantilla
                  </CButton>
                </CCardBody>
              </CCard>
            </CCol>
          ))}
        </CRow>
      </CModalBody>
      <CModalFooter>
        <CButton color="secondary" onClick={onClose}>
          Cancelar
        </CButton>
      </CModalFooter>
    </CModal>
  )
}

TemplatePickerModal.propTypes = {
  visible: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onSelect: PropTypes.func.isRequired,
}

export default TemplatePickerModal
