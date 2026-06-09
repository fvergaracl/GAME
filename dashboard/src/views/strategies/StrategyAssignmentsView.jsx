// Strategy assignments admin view.
// Reworked for scale: server-side pagination + search instead
// of pulling every game with page_size=all, plus multi-select bulk
// reassignment with a confirmation/impact step.
//
// Lists Games in the realm with their current strategyId. Expanding a
// row reveals its tasks so the same picker can reassign a strategy at
// task granularity. Checkboxes select games on the current page for a
// single bulk reassignment.
//
//   1. Load a page of games via /v1/games (page/search) + the label
//      index (built-ins + customs) once for resolving "custom:<uuid>".
//   2. On "Cambiar" / "Reasignar N" → open StrategyPickerModal.
//   3. On select → confirmation step → PATCH the game(s)/task and patch
//      local state so the change is visible without a full reload.

import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import {
  CAlert,
  CBadge,
  CButton,
  CCard,
  CCardBody,
  CCardHeader,
  CCollapse,
  CFormCheck,
  CFormInput,
  CFormSelect,
  CModal,
  CModalBody,
  CModalFooter,
  CModalHeader,
  CModalTitle,
  CProgress,
  CSpinner,
  CTable,
  CTableBody,
  CTableDataCell,
  CTableHead,
  CTableHeaderCell,
  CTableRow,
} from '@coreui/react'

import {
  listBuiltInStrategies,
  listCustomStrategies,
  listGames,
  listGameTasks,
  patchGameStrategy,
  patchTaskStrategy,
} from '../../api'
import { extractError } from '../../utils/errors'
import { SkeletonTable } from '../../components/Skeleton'
import { useToast } from '../../components/Toast'
import GlossaryHint from './glossary/GlossaryHint'
import OnboardingTour from './OnboardingTour'
import StrategyPickerModal from './StrategyPickerModal'

// Per-view tour storage key (mirror of the Library one).
export const ASSIGNMENTS_TOUR_STORAGE_KEY = 'gd-assignments-tour-seen'

const ASSIGNMENTS_TOUR_STEPS = [
  { target: '[data-tour="assignments-intro"]', i18n: 'intro', placement: 'bottom' },
  { target: '[data-tour="assignments-search"]', i18n: 'search', placement: 'bottom' },
  { target: '[data-tour="assignments-selection"]', i18n: 'selection', placement: 'right' },
  { target: '[data-tour="assignments-change"]', i18n: 'change', placement: 'left' },
  { target: '[data-tour="assignments-help"]', i18n: 'help', placement: 'bottom' },
]

const PAGE_SIZE_OPTIONS = [10, 20, 50]

// Pre-build a lookup so rendering "custom:<uuid>" reads as
// "MyStrategy v3" without doing N round-trips per row.
const buildStrategyLabelIndex = (builtIns, customs) => {
  const index = new Map()
  for (const row of builtIns) {
    index.set(row.id, { label: row.name || row.id, kind: 'BUILT_IN' })
  }
  for (const row of customs) {
    index.set(`custom:${row.id}`, {
      label: `${row.name} v${row.version}`,
      kind: row.type,
      status: row.status,
    })
  }
  return index
}

const StrategyAssignmentsView = () => {
  const { t } = useTranslation('strategies')
  // Shared feedback channel - see ToastProvider in
  // DefaultLayout. Falls back to no-ops outside a provider.
  const toast = useToast()
  const [tourRunRequest, setTourRunRequest] = useState('auto')
  const [games, setGames] = useState([])
  const [totalCount, setTotalCount] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')

  const [labelIndex, setLabelIndex] = useState(new Map())
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  // Per-game state: expanded rows + their tasks (lazy-loaded), and
  // the picker target (which game/task is about to be reassigned).
  const [expanded, setExpanded] = useState(() => new Set())
  const [tasksByGame, setTasksByGame] = useState({})
  const [tasksLoading, setTasksLoading] = useState({})
  const [actionError, setActionError] = useState(null)
  const [actionSuccess, setActionSuccess] = useState(null)

  // Selection is scoped to the current page: it resets on page/search
  // changes so the skip-already-assigned filter always has the current
  // strategyId of every selected game in hand.
  const [selected, setSelected] = useState(() => new Set())

  // pickerTarget drives the picker modal; on select we stash the chosen
  // id in pendingReassign and surface a confirmation before writing.
  const [pickerTarget, setPickerTarget] = useState(null)
  const [pendingReassign, setPendingReassign] = useState(null)
  const [bulkProgress, setBulkProgress] = useState(null)

  // Debounce the search box so typing doesn't fire a request per keystroke.
  useEffect(() => {
    const handle = setTimeout(() => {
      setSearch(searchInput.trim())
      setPage(1)
    }, 300)
    return () => clearTimeout(handle)
  }, [searchInput])

  // Label index: built-ins + customs (PUBLISHED for assignability, plus
  // the rest so a game still pointing at a DRAFT/ARCHIVED id renders a
  // name instead of a raw UUID). Loaded once, independent of pagination.
  useEffect(() => {
    let cancelled = false
    Promise.all([
      listBuiltInStrategies(),
      listCustomStrategies({ status: 'PUBLISHED', limit: 500 }),
      listCustomStrategies({ limit: 500 }),
    ])
      .then(([builtIns, publishedCustoms, allCustoms]) => {
        if (cancelled) return
        const merged = new Map()
        for (const row of allCustoms || []) merged.set(row.id, row)
        for (const row of publishedCustoms || []) merged.set(row.id, row)
        setLabelIndex(buildStrategyLabelIndex(builtIns || [], [...merged.values()]))
      })
      .catch((err) => {
        if (cancelled) return
        setError(extractError(err, 'No se pudo cargar el índice de estrategias.'))
      })
    return () => {
      cancelled = true
    }
  }, [])

  const reloadGames = useCallback(() => {
    let cancelled = false
    setIsLoading(true)
    setError(null)
    listGames({ page, pageSize, externalGameId: search || undefined })
      .then((result) => {
        if (cancelled) return
        setGames(result?.items || [])
        setTotalCount(result?.search_options?.total_count || 0)
        // New page / new search → drop the previous page's selection.
        setSelected(new Set())
      })
      .catch((err) => {
        if (cancelled) return
        setError(extractError(err, 'No se pudieron cargar las asignaciones.'))
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [page, pageSize, search])

  useEffect(() => {
    const cleanup = reloadGames()
    return cleanup
  }, [reloadGames])

  const loadTasksForGame = useCallback(async (gameId) => {
    setTasksLoading((prev) => ({ ...prev, [gameId]: true }))
    try {
      const response = await listGameTasks(gameId)
      const items = response?.items || []
      setTasksByGame((prev) => ({ ...prev, [gameId]: items }))
    } catch (err) {
      setActionError(extractError(err, `No se pudieron cargar las tasks de ${gameId}.`))
    } finally {
      setTasksLoading((prev) => ({ ...prev, [gameId]: false }))
    }
  }, [])

  const toggleExpand = useCallback(
    (gameId) => {
      setExpanded((prev) => {
        const next = new Set(prev)
        if (next.has(gameId)) {
          next.delete(gameId)
        } else {
          next.add(gameId)
          if (!tasksByGame[gameId]) {
            loadTasksForGame(gameId)
          }
        }
        return next
      })
    },
    [loadTasksForGame, tasksByGame],
  )

  const toggleSelect = useCallback((gameId) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(gameId)) next.delete(gameId)
      else next.add(gameId)
      return next
    })
  }, [])

  const allOnPageSelected = games.length > 0 && games.every((g) => selected.has(g.gameId))

  const toggleSelectAllOnPage = useCallback(() => {
    setSelected((prev) => {
      const next = new Set(prev)
      const everySelected = games.length > 0 && games.every((g) => next.has(g.gameId))
      if (everySelected) {
        for (const g of games) next.delete(g.gameId)
      } else {
        for (const g of games) next.add(g.gameId)
      }
      return next
    })
  }, [games])

  const renderStrategyLabel = useCallback(
    (strategyId) => {
      if (!strategyId) return <span className="text-medium-emphasis">-</span>
      const entry = labelIndex.get(strategyId)
      if (entry) {
        return (
          <span>
            <code className="me-2">{entry.label}</code>
            <CBadge color={entry.kind === 'BUILT_IN' ? 'info' : 'success'}>{entry.kind}</CBadge>
            {entry.status && entry.status !== 'PUBLISHED' && (
              <CBadge color="warning" className="ms-1">
                {entry.status}
              </CBadge>
            )}
          </span>
        )
      }
      return (
        <span>
          <code className="me-2">{strategyId}</code>
          <CBadge color="secondary">desconocida</CBadge>
        </span>
      )
    },
    [labelIndex],
  )

  const labelFor = useCallback(
    (strategyId) => {
      if (!strategyId) return '-'
      return labelIndex.get(strategyId)?.label || strategyId
    },
    [labelIndex],
  )

  // Picker → stash the chosen id and raise a confirmation instead of
  // writing immediately, so the admin sees what's about to change.
  const handlePickerSelect = useCallback(
    (newStrategyId) => {
      if (!pickerTarget) return
      setPendingReassign({ ...pickerTarget, newStrategyId })
    },
    [pickerTarget],
  )

  const applySingleGame = useCallback(async (gameId, newStrategyId) => {
    await patchGameStrategy(gameId, newStrategyId)
    setGames((prev) =>
      prev.map((g) => (g.gameId === gameId ? { ...g, strategyId: newStrategyId } : g)),
    )
  }, [])

  const applyTask = useCallback(async (gameId, taskId, newStrategyId) => {
    await patchTaskStrategy(gameId, taskId, newStrategyId)
    setTasksByGame((prev) => ({
      ...prev,
      [gameId]: (prev[gameId] || []).map((t) =>
        t.id === taskId ? { ...t, strategyId: newStrategyId } : t,
      ),
    }))
  }, [])

  const executeReassign = useCallback(async () => {
    if (!pendingReassign) return
    const { kind, newStrategyId } = pendingReassign
    setActionError(null)
    setActionSuccess(null)

    if (kind === 'game') {
      try {
        await applySingleGame(pendingReassign.gameId, newStrategyId)
        const msg = 'Estrategia del game actualizada.'
        setActionSuccess(msg)
        toast.success(msg)
      } catch (err) {
        const msg = extractError(err, 'No se pudo actualizar la asignación.')
        setActionError(msg)
        toast.error(msg)
      } finally {
        setPendingReassign(null)
      }
      return
    }

    if (kind === 'task') {
      try {
        await applyTask(pendingReassign.gameId, pendingReassign.taskId, newStrategyId)
        const msg = 'Estrategia de la task actualizada.'
        setActionSuccess(msg)
        toast.success(msg)
      } catch (err) {
        const msg = extractError(err, 'No se pudo actualizar la asignación.')
        setActionError(msg)
        toast.error(msg)
      } finally {
        setPendingReassign(null)
      }
      return
    }

    // Bulk: skip games already on the target so the backend's
    // "no difference" guard doesn't report them as failures.
    const targets = games.filter((g) => selected.has(g.gameId) && g.strategyId !== newStrategyId)
    const skipped = selected.size - targets.length
    const failed = []
    setBulkProgress({ total: targets.length, done: 0 })
    for (let i = 0; i < targets.length; i += 1) {
      const game = targets[i]
      try {
        await applySingleGame(game.gameId, newStrategyId)
      } catch (err) {
        failed.push({
          externalGameId: game.externalGameId,
          error: extractError(err, 'error'),
        })
      }
      setBulkProgress({ total: targets.length, done: i + 1 })
    }
    setBulkProgress(null)
    setPendingReassign(null)
    setSelected(new Set())
    const ok = targets.length - failed.length
    const parts = [`${ok} game${ok === 1 ? '' : 's'} reasignado${ok === 1 ? '' : 's'}.`]
    if (skipped > 0) parts.push(`${skipped} ya tenían esa estrategia.`)
    if (failed.length > 0) {
      setActionError(
        `${failed.length} fallaron: ${failed
          .map((f) => `${f.externalGameId} (${f.error})`)
          .join('; ')}`,
      )
    }
    const summary = parts.join(' ')
    setActionSuccess(summary)
    if (failed.length === 0) toast.success(summary)
    else toast.warning(summary)
  }, [pendingReassign, games, selected, applySingleGame, applyTask, toast])

  const totalPages = Math.max(1, Math.ceil(totalCount / pageSize))
  const customCountOnPage = useMemo(
    () => games.filter((g) => String(g.strategyId || '').startsWith('custom:')).length,
    [games],
  )

  const confirmTargetLabel = pendingReassign ? labelFor(pendingReassign.newStrategyId) : ''

  return (
    <CCard>
      <OnboardingTour
        storageKey={ASSIGNMENTS_TOUR_STORAGE_KEY}
        steps={ASSIGNMENTS_TOUR_STEPS}
        i18nNamespace="strategies"
        keyPrefix="assignments."
        welcomeKey="welcome"
        runRequest={tourRunRequest}
        onFinished={() => setTourRunRequest(null)}
      />
      <CCardHeader className="d-flex justify-content-between align-items-start gap-2 flex-wrap">
        <div data-tour="assignments-intro">
          <h4 className="mb-1">Asignación de estrategias</h4>
          <small className="text-medium-emphasis">
            Cambia la estrategia activa de un Game o de una Task. Selecciona varios games para
            reasignarlos en bloque. Las custom strategies disponibles son las publicadas en tu
            realm.
          </small>
        </div>
        <div data-tour="assignments-help">
          <CButton
            color="link"
            size="sm"
            className="px-1 text-decoration-none"
            onClick={() => setTourRunRequest('manual')}
          >
            {t('assignments.showTour')}
          </CButton>
        </div>
      </CCardHeader>
      <CCardBody>
        <div className="d-flex flex-wrap gap-2 align-items-end mb-3" data-tour="assignments-search">
          <div style={{ minWidth: 240, flex: '1 1 240px' }}>
            <label className="form-label small text-medium-emphasis">
              Buscar por External Game ID
            </label>
            <CFormInput
              type="search"
              placeholder="game-readme-001…"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
            />
          </div>
          <div style={{ width: 130 }}>
            <label className="form-label small text-medium-emphasis">Por página</label>
            <CFormSelect
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value))
                setPage(1)
              }}
            >
              {PAGE_SIZE_OPTIONS.map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </CFormSelect>
          </div>
        </div>

        {error && <CAlert color="danger">{error}</CAlert>}
        {actionError && (
          <CAlert color="warning" dismissible onClose={() => setActionError(null)}>
            {actionError}
          </CAlert>
        )}
        {actionSuccess && (
          <CAlert color="success" dismissible onClose={() => setActionSuccess(null)}>
            {actionSuccess}
          </CAlert>
        )}

        {selected.size > 0 && (
          <CAlert
            color="primary"
            className="d-flex flex-wrap justify-content-between align-items-center gap-2"
          >
            <span>
              {selected.size} game{selected.size === 1 ? '' : 's'} seleccionado
              {selected.size === 1 ? '' : 's'} en esta página.
            </span>
            <span className="d-flex gap-2">
              <CButton size="sm" color="primary" onClick={() => setPickerTarget({ kind: 'bulk' })}>
                Reasignar seleccionados
              </CButton>
              <CButton
                size="sm"
                color="secondary"
                variant="outline"
                onClick={() => setSelected(new Set())}
              >
                Limpiar
              </CButton>
            </span>
          </CAlert>
        )}

        {isLoading && (
          // Skeleton matches the Games table (checkbox +
          // expand + 3 columns + action) so the layout stays stable
          // across the loading-to-loaded transition.
          <SkeletonTable columns={5} rows={pageSize > 10 ? 8 : pageSize} hasActions />
        )}

        {!isLoading && !error && totalCount === 0 && (
          <CAlert color="info">
            <p className="mb-2">
              {search ? 'Ningún game coincide con la búsqueda.' : 'No hay games en este realm.'}
            </p>
            <CButton
              color="link"
              className="px-1 text-decoration-none"
              onClick={() => setTourRunRequest('manual')}
            >
              {t('assignments.empty.tourLink')}
            </CButton>
          </CAlert>
        )}

        {!isLoading && games.length > 0 && (
          <>
            <p className="text-medium-emphasis mb-2">
              {totalCount} game{totalCount === 1 ? '' : 's'} en total · {customCountOnPage} con
              custom strategy en esta página.
            </p>
            <CTable hover responsive align="middle">
              <CTableHead>
                <CTableRow>
                  <CTableHeaderCell style={{ width: 36 }} data-tour="assignments-selection">
                    <CFormCheck
                      checked={allOnPageSelected}
                      onChange={toggleSelectAllOnPage}
                      aria-label="Seleccionar todos en la página"
                    />
                  </CTableHeaderCell>
                  <CTableHeaderCell style={{ width: 40 }} />
                  <CTableHeaderCell>External Game ID</CTableHeaderCell>
                  <CTableHeaderCell>Platform</CTableHeaderCell>
                  <CTableHeaderCell>
                    Estrategia
                    <GlossaryHint term="assignment" />
                  </CTableHeaderCell>
                  <CTableHeaderCell style={{ width: 120 }}>Acción</CTableHeaderCell>
                </CTableRow>
              </CTableHead>
              <CTableBody>
                {games.map((game, gameIdx) => {
                  const isOpen = expanded.has(game.gameId)
                  const taskRows = tasksByGame[game.gameId] || []
                  const isLoadingTasks = !!tasksLoading[game.gameId]
                  const isFirstGame = gameIdx === 0
                  return (
                    <React.Fragment key={game.gameId}>
                      <CTableRow>
                        <CTableDataCell>
                          <CFormCheck
                            checked={selected.has(game.gameId)}
                            onChange={() => toggleSelect(game.gameId)}
                            aria-label={`Seleccionar ${game.externalGameId}`}
                          />
                        </CTableDataCell>
                        <CTableDataCell>
                          <CButton
                            size="sm"
                            color="secondary"
                            variant="ghost"
                            onClick={() => toggleExpand(game.gameId)}
                            title={isOpen ? 'Colapsar tasks' : 'Ver tasks'}
                          >
                            {isOpen ? '▾' : '▸'}
                          </CButton>
                        </CTableDataCell>
                        <CTableDataCell>
                          <code>{game.externalGameId}</code>
                        </CTableDataCell>
                        <CTableDataCell>{game.platform}</CTableDataCell>
                        <CTableDataCell>{renderStrategyLabel(game.strategyId)}</CTableDataCell>
                        <CTableDataCell
                          {...(isFirstGame ? { 'data-tour': 'assignments-change' } : {})}
                        >
                          <CButton
                            size="sm"
                            color="primary"
                            onClick={() =>
                              setPickerTarget({
                                kind: 'game',
                                gameId: game.gameId,
                                externalGameId: game.externalGameId,
                                currentStrategyId: game.strategyId,
                              })
                            }
                          >
                            Cambiar
                          </CButton>
                        </CTableDataCell>
                      </CTableRow>
                      <CTableRow>
                        <CTableDataCell colSpan={6} className="p-0 border-0">
                          <CCollapse visible={isOpen}>
                            <div className="p-3 bg-body-tertiary">
                              {isLoadingTasks && (
                                <div className="d-flex align-items-center gap-2">
                                  <CSpinner size="sm" /> Cargando tasks…
                                </div>
                              )}
                              {!isLoadingTasks && taskRows.length === 0 && (
                                <small className="text-medium-emphasis">Sin tasks asociadas.</small>
                              )}
                              {!isLoadingTasks && taskRows.length > 0 && (
                                <CTable size="sm" responsive className="mb-0">
                                  <CTableHead>
                                    <CTableRow>
                                      <CTableHeaderCell>External Task ID</CTableHeaderCell>
                                      <CTableHeaderCell>Estrategia</CTableHeaderCell>
                                      <CTableHeaderCell style={{ width: 120 }}>
                                        Acción
                                      </CTableHeaderCell>
                                    </CTableRow>
                                  </CTableHead>
                                  <CTableBody>
                                    {taskRows.map((task) => (
                                      <CTableRow key={task.id}>
                                        <CTableDataCell>
                                          <code>{task.externalTaskId}</code>
                                        </CTableDataCell>
                                        <CTableDataCell>
                                          {renderStrategyLabel(task.strategyId)}
                                        </CTableDataCell>
                                        <CTableDataCell>
                                          <CButton
                                            size="sm"
                                            color="primary"
                                            variant="outline"
                                            onClick={() =>
                                              setPickerTarget({
                                                kind: 'task',
                                                gameId: game.gameId,
                                                taskId: task.id,
                                                externalTaskId: task.externalTaskId,
                                                currentStrategyId: task.strategyId,
                                              })
                                            }
                                          >
                                            Cambiar
                                          </CButton>
                                        </CTableDataCell>
                                      </CTableRow>
                                    ))}
                                  </CTableBody>
                                </CTable>
                              )}
                            </div>
                          </CCollapse>
                        </CTableDataCell>
                      </CTableRow>
                    </React.Fragment>
                  )
                })}
              </CTableBody>
            </CTable>

            <div className="d-flex justify-content-between align-items-center mt-2">
              <CButton
                color="secondary"
                variant="outline"
                size="sm"
                disabled={page <= 1 || isLoading}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                ← Anterior
              </CButton>
              <span className="text-medium-emphasis small">
                Página {page} de {totalPages}
              </span>
              <CButton
                color="secondary"
                variant="outline"
                size="sm"
                disabled={page >= totalPages || isLoading}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              >
                Siguiente →
              </CButton>
            </div>
          </>
        )}
      </CCardBody>

      <StrategyPickerModal
        visible={!!pickerTarget}
        currentStrategyId={pickerTarget?.currentStrategyId}
        onClose={() => setPickerTarget(null)}
        onSelect={handlePickerSelect}
      />

      <CModal
        visible={!!pendingReassign}
        onClose={() => (bulkProgress ? null : setPendingReassign(null))}
      >
        <CModalHeader>
          <CModalTitle>Confirmar reasignación</CModalTitle>
        </CModalHeader>
        <CModalBody>
          {pendingReassign?.kind === 'bulk' ? (
            <>
              Vas a reasignar <strong>{selected.size}</strong> game
              {selected.size === 1 ? '' : 's'} seleccionado
              {selected.size === 1 ? '' : 's'} a <code>{confirmTargetLabel}</code>. Los que ya
              tengan esa estrategia se omiten.
            </>
          ) : pendingReassign?.kind === 'task' ? (
            <>
              La task <code>{pendingReassign?.externalTaskId}</code> pasará a{' '}
              <code>{confirmTargetLabel}</code>.
            </>
          ) : (
            <>
              El game <code>{pendingReassign?.externalGameId}</code> pasará a{' '}
              <code>{confirmTargetLabel}</code>.
            </>
          )}
          {bulkProgress && (
            <div className="mt-3">
              <CProgress
                value={bulkProgress.total ? (bulkProgress.done / bulkProgress.total) * 100 : 100}
              />
              <small className="text-medium-emphasis">
                {bulkProgress.done} / {bulkProgress.total}
              </small>
            </div>
          )}
        </CModalBody>
        <CModalFooter>
          <CButton
            color="secondary"
            variant="outline"
            disabled={!!bulkProgress}
            onClick={() => setPendingReassign(null)}
          >
            Cancelar
          </CButton>
          <CButton color="primary" disabled={!!bulkProgress} onClick={executeReassign}>
            {bulkProgress && <CSpinner size="sm" className="me-2" />}
            Reasignar
          </CButton>
        </CModalFooter>
      </CModal>
    </CCard>
  )
}

export default StrategyAssignmentsView
