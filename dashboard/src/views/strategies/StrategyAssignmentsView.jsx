// Sprint 9 — strategy assignments admin view.
//
// Lists every Game in the realm with its current strategyId. Expanding
// a row reveals the tasks for that game so the same picker can be used
// to reassign a strategy at task granularity.
//
// We don't build full Games/Tasks CRUD here — only what's needed to
// answer "which Game/Task runs which strategy" and "swap that strategy
// for another one". The flow:
//
//   1. Load games via /v1/games and customs/built-ins for label resolution.
//   2. On "Cambiar" → open StrategyPickerModal pre-seeded with current id.
//   3. On select → PATCH /games/{id} or /games/{id}/tasks/{tid} and patch
//      the row in local state so the user sees the change instantly.

import React, { useCallback, useEffect, useMemo, useState } from 'react'
import {
  CAlert,
  CBadge,
  CButton,
  CCard,
  CCardBody,
  CCardHeader,
  CCollapse,
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
import StrategyPickerModal from './StrategyPickerModal'

const extractError = (err, fallback) =>
  err?.response?.data?.detail || err?.message || fallback

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
  const [games, setGames] = useState([])
  const [labelIndex, setLabelIndex] = useState(new Map())
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  // Per-game state: expanded rows + their tasks (lazy-loaded), and
  // the picker target (which game/task is about to be reassigned).
  const [expanded, setExpanded] = useState(() => new Set())
  const [tasksByGame, setTasksByGame] = useState({})
  const [tasksLoading, setTasksLoading] = useState({})
  const [pickerTarget, setPickerTarget] = useState(null)
  const [actionError, setActionError] = useState(null)

  const reloadAssignments = useCallback(() => {
    let cancelled = false
    setIsLoading(true)
    setError(null)
    Promise.all([
      // page_size=all because the admin view wants the full assignment
      // map; pagination here would just hide assignments behind a "next
      // page" click without solving anything for the use case.
      listGames({ pageSize: 'all' }),
      listBuiltInStrategies(),
      // Status filter applied so the label index doesn't carry
      // not-assignable entries; the picker uses the same filter so the
      // two views agree.
      listCustomStrategies({ status: 'PUBLISHED', limit: 500 }),
      // Also pull DRAFT/ARCHIVED for label resolution — a game may
      // still point at one (e.g. before someone reassigned). Without
      // these the column would render the raw UUID.
      listCustomStrategies({ limit: 500 }),
    ])
      .then(([gameList, builtIns, publishedCustoms, allCustoms]) => {
        if (cancelled) return
        const items = gameList?.items || []
        setGames(items)
        const merged = new Map()
        for (const row of allCustoms || []) merged.set(row.id, row)
        for (const row of publishedCustoms || []) merged.set(row.id, row)
        setLabelIndex(buildStrategyLabelIndex(builtIns || [], [...merged.values()]))
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
  }, [])

  useEffect(() => {
    const cleanup = reloadAssignments()
    return cleanup
  }, [reloadAssignments])

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

  const renderStrategyLabel = useCallback(
    (strategyId) => {
      if (!strategyId) return <span className="text-medium-emphasis">—</span>
      const entry = labelIndex.get(strategyId)
      if (entry) {
        return (
          <span>
            <code className="me-2">{entry.label}</code>
            <CBadge color={entry.kind === 'BUILT_IN' ? 'info' : 'success'}>
              {entry.kind}
            </CBadge>
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

  const handlePickerSelect = useCallback(
    async (newStrategyId) => {
      if (!pickerTarget) return
      setActionError(null)
      try {
        if (pickerTarget.kind === 'game') {
          await patchGameStrategy(pickerTarget.gameId, newStrategyId)
          setGames((prev) =>
            prev.map((g) =>
              g.gameId === pickerTarget.gameId
                ? { ...g, strategyId: newStrategyId }
                : g,
            ),
          )
        } else {
          await patchTaskStrategy(
            pickerTarget.gameId,
            pickerTarget.taskId,
            newStrategyId,
          )
          setTasksByGame((prev) => ({
            ...prev,
            [pickerTarget.gameId]: (prev[pickerTarget.gameId] || []).map((t) =>
              t.id === pickerTarget.taskId
                ? { ...t, strategyId: newStrategyId }
                : t,
            ),
          }))
        }
      } catch (err) {
        setActionError(extractError(err, 'No se pudo actualizar la asignación.'))
      } finally {
        setPickerTarget(null)
      }
    },
    [pickerTarget],
  )

  const summary = useMemo(() => {
    const total = games.length
    const customCount = games.filter((g) =>
      String(g.strategyId || '').startsWith('custom:'),
    ).length
    return { total, customCount }
  }, [games])

  return (
    <CCard>
      <CCardHeader>
        <h4 className="mb-1">Asignación de estrategias</h4>
        <small className="text-medium-emphasis">
          Cambia la estrategia activa de un Game o de una Task. Las custom
          strategies disponibles son las que están publicadas en tu realm.
        </small>
      </CCardHeader>
      <CCardBody>
        {isLoading && (
          <div className="d-flex justify-content-center py-4">
            <CSpinner />
          </div>
        )}
        {error && <CAlert color="danger">{error}</CAlert>}
        {actionError && (
          <CAlert color="warning" dismissible onClose={() => setActionError(null)}>
            {actionError}
          </CAlert>
        )}
        {!isLoading && !error && games.length === 0 && (
          <CAlert color="info">No hay games en este realm.</CAlert>
        )}
        {!isLoading && games.length > 0 && (
          <>
            <p className="text-medium-emphasis mb-3">
              {summary.total} games · {summary.customCount} con custom strategy.
            </p>
            <CTable hover responsive>
              <CTableHead>
                <CTableRow>
                  <CTableHeaderCell style={{ width: 40 }} />
                  <CTableHeaderCell>External Game ID</CTableHeaderCell>
                  <CTableHeaderCell>Platform</CTableHeaderCell>
                  <CTableHeaderCell>Estrategia</CTableHeaderCell>
                  <CTableHeaderCell style={{ width: 140 }}>Acción</CTableHeaderCell>
                </CTableRow>
              </CTableHead>
              <CTableBody>
                {games.map((game) => {
                  const isOpen = expanded.has(game.gameId)
                  const taskRows = tasksByGame[game.gameId] || []
                  const isLoadingTasks = !!tasksLoading[game.gameId]
                  return (
                    <React.Fragment key={game.gameId}>
                      <CTableRow>
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
                        <CTableDataCell>
                          {renderStrategyLabel(game.strategyId)}
                        </CTableDataCell>
                        <CTableDataCell>
                          <CButton
                            size="sm"
                            color="primary"
                            onClick={() =>
                              setPickerTarget({
                                kind: 'game',
                                gameId: game.gameId,
                                currentStrategyId: game.strategyId,
                              })
                            }
                          >
                            Cambiar
                          </CButton>
                        </CTableDataCell>
                      </CTableRow>
                      <CTableRow>
                        <CTableDataCell colSpan={5} className="p-0 border-0">
                          <CCollapse visible={isOpen}>
                            <div className="p-3 bg-body-tertiary">
                              {isLoadingTasks && (
                                <div className="d-flex align-items-center gap-2">
                                  <CSpinner size="sm" /> Cargando tasks…
                                </div>
                              )}
                              {!isLoadingTasks && taskRows.length === 0 && (
                                <small className="text-medium-emphasis">
                                  Sin tasks asociadas.
                                </small>
                              )}
                              {!isLoadingTasks && taskRows.length > 0 && (
                                <CTable size="sm" responsive className="mb-0">
                                  <CTableHead>
                                    <CTableRow>
                                      <CTableHeaderCell>
                                        External Task ID
                                      </CTableHeaderCell>
                                      <CTableHeaderCell>Estrategia</CTableHeaderCell>
                                      <CTableHeaderCell style={{ width: 140 }}>
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
          </>
        )}
      </CCardBody>
      <StrategyPickerModal
        visible={!!pickerTarget}
        currentStrategyId={pickerTarget?.currentStrategyId}
        onClose={() => setPickerTarget(null)}
        onSelect={handlePickerSelect}
      />
    </CCard>
  )
}

export default StrategyAssignmentsView
