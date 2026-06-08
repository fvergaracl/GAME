// Sprint 2 — "Mis estrategias" library view.
//
// Solves discoverability: before this view a saved DRAFT was unreachable
// from the menu (the editor only offered create/template/extend/import),
// so a designer who closed the tab lost track of their work. This is the
// list/manage surface for every custom strategy in the realm.
//
// Server-side filters (status/type) re-query the API; the name search is
// client-side over the loaded page. Per-row actions cover the lifecycle:
// open in the editor, duplicate, publish/archive (admin), view history,
// export the bundle. Pagination at scale is deferred to Sprint 6 — here
// we load a generous page and filter in memory.

import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  CAlert,
  CBadge,
  CButton,
  CCard,
  CCardBody,
  CCardHeader,
  CCol,
  CDropdown,
  CDropdownDivider,
  CDropdownItem,
  CDropdownMenu,
  CDropdownToggle,
  CForm,
  CFormInput,
  CFormSelect,
  CModal,
  CModalBody,
  CModalFooter,
  CModalHeader,
  CModalTitle,
  CRow,
  CSpinner,
  CTable,
  CTableBody,
  CTableDataCell,
  CTableHead,
  CTableHeaderCell,
  CTableRow,
} from '@coreui/react'

import {
  archiveCustomStrategy,
  getCustomStrategy,
  importCustomStrategy,
  listBuiltInStrategies,
  listCustomStrategies,
  publishCustomStrategy,
} from '../../api'
import keycloak from '../../keycloak'
import { extractError } from '../../utils/errors'
import { SkeletonTable } from '../../components/Skeleton'
import { useToast } from '../../components/Toast'
import GlossaryHint from './glossary/GlossaryHint'
import OnboardingTour from './OnboardingTour'
import StrategyUsageModal from './StrategyUsageModal'
import StrategyVersionHistoryModal from './StrategyVersionHistoryModal'

// Sprint 8: per-view tour storage key. Setting this key from devtools to
// '' makes the tour auto-trigger again on the next mount, which is the
// supported way to replay an onboarding without code changes.
export const LIBRARY_TOUR_STORAGE_KEY = 'gd-library-tour-seen'

const LIBRARY_TOUR_STEPS = [
  { target: '[data-tour="library-intro"]', i18n: 'intro', placement: 'bottom' },
  { target: '[data-tour="library-filters"]', i18n: 'filters', placement: 'bottom' },
  { target: '[data-tour="library-new"]', i18n: 'newCta', placement: 'left' },
  { target: '[data-tour="library-row-actions"]', i18n: 'rowActions', placement: 'top' },
  { target: '[data-tour="library-status-header"]', i18n: 'statusBadge', placement: 'bottom' },
  { target: '[data-tour="library-help"]', i18n: 'help', placement: 'bottom' },
]

// Generous page size — real pagination/search is Sprint 6. This keeps the
// library usable for the hundreds-of-strategies range without a "next page".
const PAGE_LIMIT = 200

const STATUS_BADGE = {
  DRAFT: 'secondary',
  PUBLISHED: 'success',
  ARCHIVED: 'dark',
}

const STATUS_LABEL = {
  DRAFT: 'Borrador',
  PUBLISHED: 'Publicada',
  ARCHIVED: 'Archivada',
}

const TYPE_LABEL = {
  DSL_FULL: 'Desde cero',
  DSL_EXTEND: 'Extiende',
}

// UX-only admin hint (the server enforces require_admin on publish/archive).
// Mirrors the decoder in StrategyEditor.jsx.
const isCurrentUserAdmin = () => {
  try {
    const token = keycloak?.token
    if (!token) return false
    const payload = token.split('.')[1]
    const decoded = JSON.parse(atob(payload))
    return decoded?.resource_access?.account?.roles?.includes('AdministratorGAME') || false
  } catch {
    return false
  }
}

const formatDate = (iso) => {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleDateString()
  } catch {
    return iso
  }
}

const StrategyLibraryView = () => {
  const navigate = useNavigate()
  const isAdmin = useMemo(() => isCurrentUserAdmin(), [])
  const { t } = useTranslation('strategies')
  // Sprint 11: useToast() returns no-op handlers when no ToastProvider
  // is mounted (e.g. test harnesses), so this is safe to call
  // unconditionally without forcing every caller to opt-in.
  const toast = useToast()

  // 'auto' on mount honours the localStorage flag (only first-time
  // visitors see the tour); 'manual' is triggered from the
  // "Volver a ver el tour" link in the header and on the empty state.
  const [tourRunRequest, setTourRunRequest] = useState('auto')

  const [strategies, setStrategies] = useState([])
  const [builtInIndex, setBuiltInIndex] = useState(new Map())
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  const [statusFilter, setStatusFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [nameQuery, setNameQuery] = useState('')

  const [actionError, setActionError] = useState(null)
  const [actionSuccess, setActionSuccess] = useState(null)
  const [busyId, setBusyId] = useState(null)

  // { id, action: 'publish' | 'archive', name, version }
  const [confirmAction, setConfirmAction] = useState(null)
  const [historyTarget, setHistoryTarget] = useState(null)
  // { id, name } of the strategy whose consumers we're inspecting.
  const [usageTarget, setUsageTarget] = useState(null)

  const reload = useCallback(() => {
    let cancelled = false
    setIsLoading(true)
    setError(null)
    Promise.all([
      listCustomStrategies({
        status: statusFilter || undefined,
        type: typeFilter || undefined,
        limit: PAGE_LIMIT,
      }),
      listBuiltInStrategies(),
    ])
      .then(([rows, builtIns]) => {
        if (cancelled) return
        setStrategies(Array.isArray(rows) ? rows : [])
        const index = new Map()
        for (const b of builtIns || []) index.set(b.id, b.name || b.id)
        setBuiltInIndex(index)
      })
      .catch((err) => {
        if (cancelled) return
        setError(extractError(err, 'No se pudieron cargar las estrategias.'))
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [statusFilter, typeFilter])

  useEffect(() => {
    const cleanup = reload()
    return cleanup
  }, [reload])

  const visibleRows = useMemo(() => {
    const q = nameQuery.trim().toLowerCase()
    if (!q) return strategies
    return strategies.filter((s) => (s.name || '').toLowerCase().includes(q))
  }, [strategies, nameQuery])

  const parentLabel = useCallback(
    (parentStrategyId) => {
      if (!parentStrategyId) return '—'
      return builtInIndex.get(parentStrategyId) || parentStrategyId
    },
    [builtInIndex],
  )

  const handleDuplicate = useCallback(
    async (row) => {
      setActionError(null)
      setActionSuccess(null)
      setBusyId(row.id)
      try {
        // The list rows already carry astJson/blocklyXml, but re-fetch so a
        // future lighter list payload wouldn't silently duplicate an empty
        // program. The import endpoint auto-renames on name collision.
        const full = await getCustomStrategy(row.id)
        const created = await importCustomStrategy({
          name: `${full.name} (copia)`,
          description: full.description || null,
          type: full.type,
          parentStrategyId: full.parentStrategyId || null,
          astJson: full.astJson,
          blocklyXml: full.blocklyXml || null,
        })
        const msg = `Duplicada como «${created.name}» (borrador v${created.version}).`
        setActionSuccess(msg)
        toast.success(msg)
        reload()
      } catch (err) {
        const msg = extractError(err, 'No se pudo duplicar la estrategia.')
        setActionError(msg)
        toast.error(msg)
      } finally {
        setBusyId(null)
      }
    },
    [reload, toast],
  )

  const handleExport = useCallback(async (row) => {
    setActionError(null)
    setActionSuccess(null)
    setBusyId(row.id)
    try {
      const full = await getCustomStrategy(row.id)
      const bundle = {
        name: full.name,
        description: full.description || null,
        type: full.type,
        parentStrategyId: full.parentStrategyId || null,
        astJson: full.astJson,
        blocklyXml: full.blocklyXml || null,
        exportedAt: new Date().toISOString(),
        exportedFromVersion: full.version,
      }
      const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: 'application/json' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      const safeName =
        (full.name || 'strategy').replace(/[^A-Za-z0-9_-]+/g, '_').slice(0, 60) || 'strategy'
      link.download = `${safeName}.json`
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      const msg = extractError(err, 'No se pudo exportar la estrategia.')
      setActionError(msg)
      toast.error(msg)
    } finally {
      setBusyId(null)
    }
  }, [toast])

  const handleConfirmLifecycle = useCallback(async () => {
    if (!confirmAction) return
    const { id, action } = confirmAction
    setActionError(null)
    setActionSuccess(null)
    setBusyId(id)
    try {
      const updated =
        action === 'publish' ? await publishCustomStrategy(id) : await archiveCustomStrategy(id)
      const msg =
        action === 'publish'
          ? `«${updated.name}» publicada (v${updated.version}). Ahora es la versión en producción.`
          : `«${updated.name}» archivada (v${updated.version}).`
      setActionSuccess(msg)
      toast.success(msg)
      reload()
    } catch (err) {
      const msg = extractError(
        err,
        action === 'publish'
          ? 'No se pudo publicar la estrategia.'
          : 'No se pudo archivar la estrategia.',
      )
      setActionError(msg)
      toast.error(msg)
    } finally {
      setBusyId(null)
      setConfirmAction(null)
    }
  }, [confirmAction, reload, toast])

  // Server-side filters (re-query) vs. the full client-side filter set.
  const serverFiltersActive = Boolean(statusFilter || typeFilter)
  const hasFiltersActive = serverFiltersActive || Boolean(nameQuery.trim())
  const noResults = !isLoading && !error && visibleRows.length === 0

  return (
    <CCard>
      <OnboardingTour
        storageKey={LIBRARY_TOUR_STORAGE_KEY}
        steps={LIBRARY_TOUR_STEPS}
        i18nNamespace="strategies"
        keyPrefix="library."
        welcomeKey="welcome"
        runRequest={tourRunRequest}
        onFinished={() => setTourRunRequest(null)}
      />
      <CCardHeader className="d-flex justify-content-between align-items-center">
        <div data-tour="library-intro">
          <h4 className="mb-1">Mis estrategias</h4>
          <small className="text-medium-emphasis">
            Todas las estrategias personalizadas de tu realm. Ábrelas para seguir editando,
            duplícalas como punto de partida o publícalas para que puedan asignarse a juegos y
            tareas.
          </small>
        </div>
        <div className="d-flex align-items-center gap-2" data-tour="library-help">
          <CButton
            color="link"
            size="sm"
            className="px-1 text-decoration-none"
            onClick={() => setTourRunRequest('manual')}
          >
            {t('library.showTour')}
          </CButton>
          <CButton
            color="primary"
            data-tour="library-new"
            onClick={() => navigate('/strategies/editor')}
          >
            Nueva estrategia
          </CButton>
        </div>
      </CCardHeader>
      <CCardBody>
        <CForm className="mb-3" data-tour="library-filters">
          <CRow className="g-2 align-items-end">
            <CCol md={4}>
              <label className="form-label small text-medium-emphasis">Buscar por nombre</label>
              <CFormInput
                type="search"
                placeholder="Nombre de la estrategia…"
                value={nameQuery}
                onChange={(e) => setNameQuery(e.target.value)}
              />
            </CCol>
            <CCol md={3}>
              <label className="form-label small text-medium-emphasis">Estado</label>
              <CFormSelect value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
                <option value="">Todos</option>
                <option value="DRAFT">Borrador</option>
                <option value="PUBLISHED">Publicada</option>
                <option value="ARCHIVED">Archivada</option>
              </CFormSelect>
            </CCol>
            <CCol md={3}>
              <label className="form-label small text-medium-emphasis">Tipo</label>
              <CFormSelect value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
                <option value="">Todos</option>
                <option value="DSL_FULL">Desde cero</option>
                <option value="DSL_EXTEND">Extiende</option>
              </CFormSelect>
            </CCol>
            <CCol md={2}>
              <CButton
                color="secondary"
                variant="outline"
                className="w-100"
                onClick={() => reload()}
                disabled={isLoading}
              >
                Refrescar
              </CButton>
            </CCol>
          </CRow>
        </CForm>

        {actionError && (
          <CAlert color="danger" dismissible onClose={() => setActionError(null)}>
            {actionError}
          </CAlert>
        )}
        {actionSuccess && (
          <CAlert color="success" dismissible onClose={() => setActionSuccess(null)}>
            {actionSuccess}
          </CAlert>
        )}
        {error && <CAlert color="danger">{error}</CAlert>}

        {isLoading && (
          // Sprint 9: skeleton preserves the table layout so the swap to
          // real rows doesn't shift the viewport.
          <SkeletonTable columns={7} rows={5} hasActions />
        )}

        {noResults && hasFiltersActive && (
          <CAlert color="info">No hay estrategias que coincidan con los filtros.</CAlert>
        )}

        {noResults && !hasFiltersActive && (
          <CAlert color="info">
            <p className="mb-2">
              Todavía no has creado ninguna estrategia. Empieza desde cero o a partir de una
              plantilla.
            </p>
            <div className="d-flex flex-wrap gap-2 align-items-center">
              <CButton color="primary" onClick={() => navigate('/strategies/editor')}>
                Crear mi primera estrategia
              </CButton>
              <CButton
                color="link"
                className="px-1 text-decoration-none"
                onClick={() => setTourRunRequest('manual')}
              >
                {t('library.empty.tourLink')}
              </CButton>
            </div>
          </CAlert>
        )}

        {!isLoading && visibleRows.length > 0 && (
          <>
            <p className="text-medium-emphasis mb-2">
              {visibleRows.length}
              {hasFiltersActive ? ` de ${strategies.length}` : ''} estrategia
              {visibleRows.length === 1 ? '' : 's'}.
            </p>
            <CTable hover responsive align="middle">
              <CTableHead>
                <CTableRow>
                  <CTableHeaderCell>Nombre</CTableHeaderCell>
                  <CTableHeaderCell>
                    Tipo
                    <GlossaryHint term="dslFull" />
                  </CTableHeaderCell>
                  <CTableHeaderCell data-tour="library-status-header">
                    Estado
                    <GlossaryHint term="lifecycle" />
                  </CTableHeaderCell>
                  <CTableHeaderCell style={{ width: 70 }}>Versión</CTableHeaderCell>
                  <CTableHeaderCell>
                    Padre
                    <GlossaryHint term="parentStrategy" />
                  </CTableHeaderCell>
                  <CTableHeaderCell>Fecha</CTableHeaderCell>
                  <CTableHeaderCell>Autor</CTableHeaderCell>
                  <CTableHeaderCell style={{ width: 200 }}>Acciones</CTableHeaderCell>
                </CTableRow>
              </CTableHead>
              <CTableBody>
                {visibleRows.map((row, rowIdx) => {
                  const canPublish = isAdmin && row.status === 'DRAFT'
                  const canArchive =
                    isAdmin && (row.status === 'DRAFT' || row.status === 'PUBLISHED')
                  const isRowBusy = busyId === row.id
                  // Anchor the row-actions tour step on the first row so it
                  // exists even when only one strategy has been created.
                  const isFirst = rowIdx === 0
                  return (
                    <CTableRow key={row.id}>
                      <CTableDataCell>
                        <div className="fw-semibold">{row.name}</div>
                        {row.description && (
                          <small className="text-medium-emphasis">{row.description}</small>
                        )}
                      </CTableDataCell>
                      <CTableDataCell>
                        <CBadge color={row.type === 'DSL_EXTEND' ? 'warning' : 'info'}>
                          {TYPE_LABEL[row.type] || row.type}
                        </CBadge>
                        <GlossaryHint term={row.type === 'DSL_EXTEND' ? 'dslExtend' : 'dslFull'} />
                      </CTableDataCell>
                      <CTableDataCell>
                        <CBadge color={STATUS_BADGE[row.status] || 'secondary'}>
                          {STATUS_LABEL[row.status] || row.status}
                        </CBadge>
                        <GlossaryHint
                          term={
                            row.status === 'PUBLISHED'
                              ? 'published'
                              : row.status === 'ARCHIVED'
                                ? 'archived'
                                : 'draft'
                          }
                        />
                      </CTableDataCell>
                      <CTableDataCell>v{row.version}</CTableDataCell>
                      <CTableDataCell>
                        {row.type === 'DSL_EXTEND' ? (
                          <code>{parentLabel(row.parentStrategyId)}</code>
                        ) : (
                          <span className="text-medium-emphasis">—</span>
                        )}
                      </CTableDataCell>
                      <CTableDataCell>{formatDate(row.created_at)}</CTableDataCell>
                      <CTableDataCell>
                        {row.createdBy ? (
                          <small>
                            <code>{row.createdBy}</code>
                          </small>
                        ) : (
                          <span className="text-medium-emphasis">—</span>
                        )}
                      </CTableDataCell>
                      <CTableDataCell {...(isFirst ? { 'data-tour': 'library-row-actions' } : {})}>
                        <div className="d-flex gap-2 align-items-center">
                          <CButton
                            size="sm"
                            color="primary"
                            onClick={() => navigate(`/strategies/editor/${row.id}`)}
                          >
                            Abrir
                          </CButton>
                          <CDropdown variant="btn-group" portal>
                            <CDropdownToggle
                              size="sm"
                              color="secondary"
                              variant="outline"
                              disabled={isRowBusy}
                            >
                              {isRowBusy ? <CSpinner size="sm" /> : 'Acciones'}
                            </CDropdownToggle>
                            <CDropdownMenu>
                              <CDropdownItem
                                component="button"
                                onClick={() => handleDuplicate(row)}
                              >
                                Duplicar
                              </CDropdownItem>
                              <CDropdownItem
                                component="button"
                                onClick={() => setHistoryTarget(row.id)}
                              >
                                Ver historial
                              </CDropdownItem>
                              <CDropdownItem
                                component="button"
                                onClick={() => setUsageTarget({ id: row.id, name: row.name })}
                              >
                                ¿Dónde se usa?
                              </CDropdownItem>
                              <CDropdownItem component="button" onClick={() => handleExport(row)}>
                                Exportar JSON
                              </CDropdownItem>
                              {(canPublish || canArchive) && <CDropdownDivider />}
                              {canPublish && (
                                <CDropdownItem
                                  component="button"
                                  onClick={() =>
                                    setConfirmAction({
                                      id: row.id,
                                      action: 'publish',
                                      name: row.name,
                                      version: row.version,
                                    })
                                  }
                                >
                                  Publicar
                                </CDropdownItem>
                              )}
                              {canArchive && (
                                <CDropdownItem
                                  component="button"
                                  className="text-danger"
                                  onClick={() =>
                                    setConfirmAction({
                                      id: row.id,
                                      action: 'archive',
                                      name: row.name,
                                      version: row.version,
                                    })
                                  }
                                >
                                  Archivar
                                </CDropdownItem>
                              )}
                            </CDropdownMenu>
                          </CDropdown>
                        </div>
                      </CTableDataCell>
                    </CTableRow>
                  )
                })}
              </CTableBody>
            </CTable>
          </>
        )}
      </CCardBody>

      <CModal visible={!!confirmAction} onClose={() => setConfirmAction(null)}>
        <CModalHeader>
          <CModalTitle>
            {confirmAction?.action === 'publish'
              ? '¿Publicar esta versión?'
              : '¿Archivar esta estrategia?'}
          </CModalTitle>
        </CModalHeader>
        <CModalBody>
          {confirmAction?.action === 'publish' ? (
            <>
              Al publicar, la <strong>v{confirmAction?.version}</strong> de «{confirmAction?.name}»
              pasa a ser la versión en producción asignable a juegos y tareas. Cualquier versión
              publicada anterior con el mismo nombre se archivará automáticamente.
            </>
          ) : (
            <>
              Al archivar «{confirmAction?.name}» (v{confirmAction?.version}) queda fuera de
              circulación: ya no se podrá editar ni publicar, aunque su historial seguirá
              disponible.
            </>
          )}
        </CModalBody>
        <CModalFooter>
          <CButton
            color="secondary"
            variant="outline"
            onClick={() => setConfirmAction(null)}
            disabled={busyId === confirmAction?.id}
          >
            Cancelar
          </CButton>
          <CButton
            color={confirmAction?.action === 'publish' ? 'success' : 'dark'}
            onClick={handleConfirmLifecycle}
            disabled={busyId === confirmAction?.id}
          >
            {busyId === confirmAction?.id && <CSpinner size="sm" className="me-2" />}
            {confirmAction?.action === 'publish' ? 'Sí, publicar' : 'Sí, archivar'}
          </CButton>
        </CModalFooter>
      </CModal>

      <StrategyVersionHistoryModal
        visible={!!historyTarget}
        strategyId={historyTarget}
        isAdmin={isAdmin}
        onClose={() => setHistoryTarget(null)}
        onRollbackDone={() => {
          setHistoryTarget(null)
          reload()
        }}
      />

      <StrategyUsageModal
        visible={!!usageTarget}
        strategyId={usageTarget?.id}
        strategyName={usageTarget?.name}
        onClose={() => setUsageTarget(null)}
        onReassigned={() => reload()}
      />
    </CCard>
  )
}

export default StrategyLibraryView
