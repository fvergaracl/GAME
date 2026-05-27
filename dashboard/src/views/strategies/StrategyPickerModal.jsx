// Sprint 9 — strategy picker modal.
//
// Two-tab modal used by the admin "Asignación" view to choose which
// strategy gets assigned to a Game or one of its Tasks. Built-ins live
// alongside the realm's PUBLISHED custom strategies; DRAFT/ARCHIVED
// rows are intentionally filtered out because the backend refuses to
// assign them (see ``GameService._validate_strategy_assignment``).
//
// Renders the same CCard grid as TemplatePickerModal so the look and
// feel stay consistent with the editor's empty-state chooser.

import React, { useEffect, useMemo, useState } from 'react'
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
  CNav,
  CNavItem,
  CNavLink,
  CRow,
  CSpinner,
} from '@coreui/react'

import { listBuiltInStrategies, listCustomStrategies } from '../../api'

const TAB_BUILTIN = 'builtin'
const TAB_CUSTOM = 'custom'

const extractError = (err, fallback) =>
  err?.response?.data?.detail || err?.message || fallback

const StrategyPickerModal = ({ visible, currentStrategyId, onClose, onSelect }) => {
  const [activeTab, setActiveTab] = useState(TAB_BUILTIN)
  const [builtIns, setBuiltIns] = useState([])
  const [customs, setCustoms] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!visible) return
    let cancelled = false
    setIsLoading(true)
    setError(null)
    // Fire both lists in parallel — the modal is small and admins will
    // flip between tabs frequently, so paying both costs up-front keeps
    // tab switching instant.
    Promise.all([
      listBuiltInStrategies().catch((err) => {
        throw new Error(extractError(err, 'No se pudo cargar built-ins.'))
      }),
      listCustomStrategies({ status: 'PUBLISHED' }).catch((err) => {
        throw new Error(extractError(err, 'No se pudieron cargar las custom strategies.'))
      }),
    ])
      .then(([builtInRows, customRows]) => {
        if (cancelled) return
        setBuiltIns(Array.isArray(builtInRows) ? builtInRows : [])
        setCustoms(Array.isArray(customRows) ? customRows : [])
      })
      .catch((err) => {
        if (cancelled) return
        setError(err.message)
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [visible])

  const rows = useMemo(() => {
    if (activeTab === TAB_BUILTIN) {
      return builtIns.map((row) => ({
        key: `builtin:${row.id}`,
        assignedId: row.id,
        title: row.name || row.id,
        subtitle: row.description || 'Sin descripción.',
        meta: row.id,
        badge: { color: 'info', label: 'Built-in' },
      }))
    }
    return customs.map((row) => ({
      key: `custom:${row.id}`,
      assignedId: `custom:${row.id}`,
      title: row.name,
      subtitle: row.description || 'Sin descripción.',
      meta: `v${row.version}`,
      badge: {
        color: row.type === 'DSL_EXTEND' ? 'warning' : 'success',
        label: row.type,
      },
    }))
  }, [activeTab, builtIns, customs])

  return (
    <CModal visible={visible} onClose={onClose} size="lg">
      <CModalHeader>
        <CModalTitle>Elige una estrategia</CModalTitle>
      </CModalHeader>
      <CModalBody>
        <CNav variant="tabs" className="mb-3">
          <CNavItem>
            <CNavLink
              active={activeTab === TAB_BUILTIN}
              onClick={() => setActiveTab(TAB_BUILTIN)}
              role="button"
            >
              Built-in ({builtIns.length})
            </CNavLink>
          </CNavItem>
          <CNavItem>
            <CNavLink
              active={activeTab === TAB_CUSTOM}
              onClick={() => setActiveTab(TAB_CUSTOM)}
              role="button"
            >
              Custom (tu realm) ({customs.length})
            </CNavLink>
          </CNavItem>
        </CNav>

        {isLoading && (
          <div className="d-flex justify-content-center py-4">
            <CSpinner />
          </div>
        )}
        {error && <CAlert color="danger">{error}</CAlert>}
        {!isLoading && !error && rows.length === 0 && (
          <CAlert color="info">
            {activeTab === TAB_CUSTOM
              ? 'No hay custom strategies publicadas. Crea una desde el editor y publícala.'
              : 'No hay built-ins registradas.'}
          </CAlert>
        )}

        <CRow>
          {rows.map((row) => {
            const isCurrent = row.assignedId === currentStrategyId
            return (
              <CCol md={6} key={row.key} className="mb-3">
                <CCard
                  className="h-100"
                  style={
                    isCurrent
                      ? { borderColor: 'var(--cui-primary)', borderWidth: '2px' }
                      : undefined
                  }
                >
                  <CCardBody className="d-flex flex-column">
                    <CCardTitle className="d-flex align-items-center gap-2">
                      {row.title}
                      <CBadge color={row.badge.color}>{row.badge.label}</CBadge>
                      {isCurrent && (
                        <CBadge color="primary" className="ms-auto">
                          Actual
                        </CBadge>
                      )}
                    </CCardTitle>
                    <small className="text-medium-emphasis mb-2">
                      <code>{row.meta}</code>
                    </small>
                    <CCardText className="flex-grow-1">{row.subtitle}</CCardText>
                    <CButton
                      color={isCurrent ? 'secondary' : 'primary'}
                      disabled={isCurrent}
                      onClick={() => {
                        onSelect(row.assignedId)
                        onClose()
                      }}
                    >
                      {isCurrent ? 'Ya asignada' : 'Usar'}
                    </CButton>
                  </CCardBody>
                </CCard>
              </CCol>
            )
          })}
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

StrategyPickerModal.propTypes = {
  visible: PropTypes.bool.isRequired,
  currentStrategyId: PropTypes.string,
  onClose: PropTypes.func.isRequired,
  onSelect: PropTypes.func.isRequired,
}

StrategyPickerModal.defaultProps = {
  currentStrategyId: null,
}

export default StrategyPickerModal
