// Sprint 9 — version history modal.
//
// Renders the version timeline of a strategy family alongside a
// per-section AST diff between two selected versions, and exposes a
// "Rollback" CTA for admins. Rollback reaches the backend, which
// re-PUBLISHes the target version, archives whichever version was
// currently PUBLISHED, and cascades Games.strategyId/Tasks.strategyId
// so consumers never end up pointing at an ARCHIVED row.
//
// We render the diff as a JSON-ish text block coloured by kind rather
// than wiring two Blockly workspaces — readability for a designer
// reviewing changes is higher and it keeps the bundle smaller.

import React, { useEffect, useMemo, useState } from 'react'
import PropTypes from 'prop-types'
import {
  CAlert,
  CBadge,
  CButton,
  CCol,
  CFormSelect,
  CListGroup,
  CListGroupItem,
  CModal,
  CModalBody,
  CModalFooter,
  CModalHeader,
  CModalTitle,
  CRow,
  CSpinner,
} from '@coreui/react'

import { listStrategyVersions, rollbackStrategy } from '../../api'
import { extractError } from '../../utils/errors'
import { DIFF_KINDS, diffPrograms } from './dsl/diffAst'

const STATUS_BADGE = {
  DRAFT: 'secondary',
  PUBLISHED: 'success',
  ARCHIVED: 'dark',
}

const KIND_LABEL = {
  [DIFF_KINDS.ADDED]: 'Añadida',
  [DIFF_KINDS.REMOVED]: 'Eliminada',
  [DIFF_KINDS.MODIFIED]: 'Modificada',
  [DIFF_KINDS.UNCHANGED]: 'Sin cambios',
}

const KIND_COLOR = {
  [DIFF_KINDS.ADDED]: 'success',
  [DIFF_KINDS.REMOVED]: 'danger',
  [DIFF_KINDS.MODIFIED]: 'warning',
  [DIFF_KINDS.UNCHANGED]: 'secondary',
}

const formatDate = (iso) => {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

const prettyJson = (value) => {
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return String(value)
  }
}

const RuleDiffPanel = ({ section, entries = [] }) => {
  if (!entries || entries.length === 0) return null
  return (
    <div className="mb-3">
      <h6 className="text-uppercase text-medium-emphasis">{section}</h6>
      {entries.map((entry) => (
        <div
          key={`${section}-${entry.id}`}
          className={`p-2 mb-2 border rounded bg-${KIND_COLOR[entry.kind]}-subtle`}
        >
          <div className="d-flex align-items-center mb-2">
            <CBadge color={KIND_COLOR[entry.kind]} className="me-2">
              {KIND_LABEL[entry.kind]}
            </CBadge>
            <code>{entry.id}</code>
          </div>
          {entry.kind === DIFF_KINDS.MODIFIED && (
            <CRow>
              <CCol md={6}>
                <small className="text-medium-emphasis">Antes</small>
                <pre
                  className="small mb-0 p-2 bg-body rounded"
                  style={{ maxHeight: '12rem', overflow: 'auto' }}
                >
                  {prettyJson(entry.a)}
                </pre>
              </CCol>
              <CCol md={6}>
                <small className="text-medium-emphasis">Después</small>
                <pre
                  className="small mb-0 p-2 bg-body rounded"
                  style={{ maxHeight: '12rem', overflow: 'auto' }}
                >
                  {prettyJson(entry.b)}
                </pre>
              </CCol>
            </CRow>
          )}
          {(entry.kind === DIFF_KINDS.ADDED || entry.kind === DIFF_KINDS.REMOVED) && (
            <pre
              className="small mb-0 p-2 bg-body rounded"
              style={{ maxHeight: '12rem', overflow: 'auto' }}
            >
              {prettyJson(entry.b ?? entry.a)}
            </pre>
          )}
        </div>
      ))}
    </div>
  )
}

RuleDiffPanel.propTypes = {
  section: PropTypes.string.isRequired,
  entries: PropTypes.array,
}

const ParentVariablesPanel = ({ entries = [] }) => {
  if (!entries || entries.length === 0) return null
  const changed = entries.filter((e) => e.kind !== DIFF_KINDS.UNCHANGED)
  if (changed.length === 0) return null
  return (
    <div className="mb-3">
      <h6 className="text-uppercase text-medium-emphasis">Parent variables</h6>
      {changed.map((entry) => (
        <div
          key={`pv-${entry.key}`}
          className={`p-2 mb-2 border rounded bg-${KIND_COLOR[entry.kind]}-subtle`}
        >
          <div className="d-flex align-items-center mb-1">
            <CBadge color={KIND_COLOR[entry.kind]} className="me-2">
              {KIND_LABEL[entry.kind]}
            </CBadge>
            <code>{entry.key}</code>
          </div>
          <div className="small">
            <code className="me-2">{JSON.stringify(entry.a)}</code>→
            <code className="ms-2">{JSON.stringify(entry.b)}</code>
          </div>
        </div>
      ))}
    </div>
  )
}

ParentVariablesPanel.propTypes = { entries: PropTypes.array }

const StrategyVersionHistoryModal = ({
  visible,
  strategyId = null,
  isAdmin = false,
  onClose,
  onRollbackDone = null,
}) => {
  const [versions, setVersions] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [rollbackError, setRollbackError] = useState(null)
  const [isRollingBack, setIsRollingBack] = useState(false)
  const [confirming, setConfirming] = useState(false)
  const [selectedAId, setSelectedAId] = useState(null)
  const [selectedBId, setSelectedBId] = useState(null)

  useEffect(() => {
    if (!visible || !strategyId) return
    let cancelled = false
    setIsLoading(true)
    setError(null)
    setRollbackError(null)
    setConfirming(false)
    listStrategyVersions(strategyId)
      .then((rows) => {
        if (cancelled) return
        const list = Array.isArray(rows) ? rows : []
        setVersions(list)
        const published = list.find((v) => v.status === 'PUBLISHED')
        const newest = list[0]
        // Default selection: A = the version the user clicked
        // (strategyId), B = whichever is PUBLISHED (or the newest if
        // none is). Falls back gracefully when the family only has
        // one row.
        setSelectedAId(strategyId || newest?.id || null)
        setSelectedBId(
          published?.id || (newest?.id !== strategyId ? newest?.id : null) || newest?.id || null,
        )
      })
      .catch((err) => {
        if (cancelled) return
        setError(extractError(err, 'No se pudo cargar el historial.'))
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [visible, strategyId])

  const selectedA = useMemo(
    () => versions.find((v) => v.id === selectedAId) || null,
    [versions, selectedAId],
  )
  const selectedB = useMemo(
    () => versions.find((v) => v.id === selectedBId) || null,
    [versions, selectedBId],
  )

  const diff = useMemo(() => {
    if (!selectedA || !selectedB) return null
    return diffPrograms(selectedA.astJson, selectedB.astJson)
  }, [selectedA, selectedB])

  const rollbackEligible =
    isAdmin && selectedA && selectedA.status !== 'PUBLISHED' && versions.length > 1

  const handleRollback = async () => {
    if (!selectedA) return
    setIsRollingBack(true)
    setRollbackError(null)
    try {
      const promoted = await rollbackStrategy(selectedA.id, selectedA.version)
      if (onRollbackDone) onRollbackDone(promoted)
    } catch (err) {
      setRollbackError(extractError(err, 'No se pudo hacer el rollback.'))
    } finally {
      setIsRollingBack(false)
      setConfirming(false)
    }
  }

  return (
    <CModal visible={visible} onClose={onClose} size="xl" scrollable>
      <CModalHeader>
        <CModalTitle>Historial de versiones</CModalTitle>
      </CModalHeader>
      <CModalBody>
        {isLoading && (
          <div className="d-flex justify-content-center py-4">
            <CSpinner />
          </div>
        )}
        {error && <CAlert color="danger">{error}</CAlert>}
        {!isLoading && !error && versions.length === 0 && (
          <CAlert color="info">Esta estrategia no tiene versiones.</CAlert>
        )}
        {!isLoading && versions.length > 0 && (
          <CRow>
            <CCol md={4}>
              <h6 className="text-uppercase text-medium-emphasis">Versiones</h6>
              <CListGroup>
                {versions.map((v) => (
                  <CListGroupItem
                    key={v.id}
                    component="button"
                    active={v.id === selectedAId}
                    onClick={() => setSelectedAId(v.id)}
                  >
                    <div className="d-flex justify-content-between align-items-start">
                      <strong>v{v.version}</strong>
                      <CBadge color={STATUS_BADGE[v.status] || 'secondary'}>{v.status}</CBadge>
                    </div>
                    <div className="small text-medium-emphasis">{formatDate(v.created_at)}</div>
                    {v.createdBy && (
                      <div className="small text-medium-emphasis">
                        Por <code>{v.createdBy}</code>
                      </div>
                    )}
                  </CListGroupItem>
                ))}
              </CListGroup>
            </CCol>
            <CCol md={8}>
              <CRow className="mb-3">
                <CCol md={6}>
                  <label className="form-label small text-medium-emphasis">
                    Versión A (origen)
                  </label>
                  <CFormSelect
                    value={selectedAId || ''}
                    onChange={(e) => setSelectedAId(e.target.value)}
                  >
                    {versions.map((v) => (
                      <option key={`a-${v.id}`} value={v.id}>
                        v{v.version} · {v.status}
                      </option>
                    ))}
                  </CFormSelect>
                </CCol>
                <CCol md={6}>
                  <label className="form-label small text-medium-emphasis">
                    Versión B (comparar contra)
                  </label>
                  <CFormSelect
                    value={selectedBId || ''}
                    onChange={(e) => setSelectedBId(e.target.value)}
                  >
                    {versions.map((v) => (
                      <option key={`b-${v.id}`} value={v.id}>
                        v{v.version} · {v.status}
                      </option>
                    ))}
                  </CFormSelect>
                </CCol>
              </CRow>
              {rollbackError && (
                <CAlert color="danger" dismissible onClose={() => setRollbackError(null)}>
                  {rollbackError}
                </CAlert>
              )}
              {confirming && (
                <CAlert color="warning">
                  Vas a re-publicar <strong>v{selectedA?.version}</strong> y archivar la versión
                  actualmente publicada. Todos los Games y Tasks que apuntaban a la versión activa
                  se redirigirán automáticamente. ¿Continuar?
                  <div className="mt-2 d-flex gap-2">
                    <CButton
                      color="danger"
                      size="sm"
                      onClick={handleRollback}
                      disabled={isRollingBack}
                    >
                      {isRollingBack ? 'Aplicando…' : 'Sí, hacer rollback'}
                    </CButton>
                    <CButton
                      color="secondary"
                      size="sm"
                      variant="outline"
                      onClick={() => setConfirming(false)}
                      disabled={isRollingBack}
                    >
                      Cancelar
                    </CButton>
                  </div>
                </CAlert>
              )}
              {diff && (
                <>
                  <div className="mb-3 d-flex gap-3 small">
                    <span>
                      <CBadge color="success">+{diff.summary.added}</CBadge> añadidas
                    </span>
                    <span>
                      <CBadge color="danger">-{diff.summary.removed}</CBadge> eliminadas
                    </span>
                    <span>
                      <CBadge color="warning">~{diff.summary.modified}</CBadge> modificadas
                    </span>
                    <span className="text-medium-emphasis">
                      ={diff.summary.unchanged} sin cambios
                    </span>
                  </div>
                  <RuleDiffPanel section="Reglas" entries={diff.rules} />
                  <RuleDiffPanel section="Pre-rules" entries={diff.pre_rules} />
                  <RuleDiffPanel section="Post-rules" entries={diff.post_rules} />
                  <ParentVariablesPanel entries={diff.parent_variables} />
                  {diff.default && diff.default.kind !== DIFF_KINDS.UNCHANGED && (
                    <RuleDiffPanel
                      section="Default"
                      entries={[{ ...diff.default, id: 'default' }]}
                    />
                  )}
                  {diff.summary.added === 0 &&
                    diff.summary.removed === 0 &&
                    diff.summary.modified === 0 && (
                      <CAlert color="info">
                        Las dos versiones son estructuralmente idénticas.
                      </CAlert>
                    )}
                </>
              )}
            </CCol>
          </CRow>
        )}
      </CModalBody>
      <CModalFooter className="d-flex justify-content-between">
        <div className="small text-medium-emphasis">
          {selectedA && (
            <>
              Seleccionada: <strong>v{selectedA.version}</strong> · {selectedA.status}
            </>
          )}
        </div>
        <div className="d-flex gap-2">
          {rollbackEligible && !confirming && (
            <CButton color="warning" onClick={() => setConfirming(true)} disabled={isRollingBack}>
              Hacer rollback a v{selectedA.version}
            </CButton>
          )}
          <CButton color="secondary" onClick={onClose} disabled={isRollingBack}>
            Cerrar
          </CButton>
        </div>
      </CModalFooter>
    </CModal>
  )
}

StrategyVersionHistoryModal.propTypes = {
  visible: PropTypes.bool.isRequired,
  strategyId: PropTypes.string,
  isAdmin: PropTypes.bool,
  onClose: PropTypes.func.isRequired,
  onRollbackDone: PropTypes.func,
}

export default StrategyVersionHistoryModal
