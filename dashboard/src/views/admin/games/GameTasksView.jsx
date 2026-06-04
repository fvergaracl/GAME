// Sprint 3 (CRUD management) — per-game task management.
//
// Reached from a game row's "Ver tareas" action (route
// /admin/games/:gameId/tasks). It lists the game's tasks and is the home for
// the task lifecycle: create, edit, duplicate, delete (dedicated modals) and
// a bulk-create flow. Mirrors GamesManagementView's refreshTick reload
// pattern, but tasks aren't server-paginated here (listGameTasks returns the
// whole set), so search is a light client-side filter over externalTaskId.
//
// The header resolves the game's externalGameId via getGame purely for a
// human label; a fetch failure there is non-blocking (we fall back to the raw
// id) since the task list is keyed on the internal gameId from the URL.

import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  CAlert,
  CButton,
  CCard,
  CCardBody,
  CCardHeader,
  CDropdown,
  CDropdownDivider,
  CDropdownItem,
  CDropdownMenu,
  CDropdownToggle,
  CFormInput,
  CTable,
  CTableBody,
  CTableDataCell,
  CTableHead,
  CTableHeaderCell,
  CTableRow,
} from '@coreui/react'
import CIcon from '@coreui/icons-react'
import { cilArrowLeft, cilLayers, cilPlus } from '@coreui/icons'

import { getGame, listGameTasks } from '../../../api'
import { extractError } from '../../../utils/errors'
import { SkeletonTable } from '../../../components/Skeleton'
import TaskFormModal from './TaskFormModal'
import TaskDuplicateModal from './TaskDuplicateModal'
import TaskDeleteDialog from './TaskDeleteDialog'
import TaskBulkModal from './TaskBulkModal'

const CLOSED_MODAL = { mode: null, task: null }

const formatDate = (value) => {
  if (!value) return '—'
  const d = new Date(value)
  return Number.isNaN(d.getTime()) ? '—' : d.toLocaleString()
}

const strategyIdOf = (task) => task?.strategy?.id || task?.strategyId || ''

const GameTasksView = () => {
  const { t } = useTranslation('management')
  const navigate = useNavigate()
  const { gameId } = useParams()

  const [game, setGame] = useState(null)
  const [tasks, setTasks] = useState([])
  const [search, setSearch] = useState('')

  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [refreshTick, setRefreshTick] = useState(0)

  const [formModal, setFormModal] = useState(CLOSED_MODAL)
  const [bulkOpen, setBulkOpen] = useState(false)
  const [duplicateTarget, setDuplicateTarget] = useState(null)
  const [deleteTarget, setDeleteTarget] = useState(null)

  // Resolve the game label once (best-effort). Independent of the task reload
  // so it doesn't re-fetch on every refreshTick bump.
  useEffect(() => {
    if (!gameId) return undefined
    let cancelled = false
    getGame(gameId)
      .then((g) => {
        if (!cancelled) setGame(g)
      })
      .catch(() => {
        if (!cancelled) setGame(null)
      })
    return () => {
      cancelled = true
    }
  }, [gameId])

  const reload = useCallback(() => {
    if (!gameId) return undefined
    let cancelled = false
    setIsLoading(true)
    setError(null)
    listGameTasks(gameId)
      .then((result) => {
        if (cancelled) return
        setTasks(result?.items || [])
      })
      .catch((err) => {
        if (cancelled) return
        setError(extractError(err, t('common.loadError')))
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [gameId, t])

  useEffect(() => {
    const cleanup = reload()
    return cleanup
  }, [reload, refreshTick])

  const externalGameId = game?.externalGameId || gameId

  const filteredTasks = useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) return tasks
    return tasks.filter((task) => (task.externalTaskId || '').toLowerCase().includes(q))
  }, [tasks, search])

  const bumpRefresh = () => setRefreshTick((n) => n + 1)

  const openCreate = () => setFormModal({ mode: 'create', task: null })
  const openEdit = (task) => setFormModal({ mode: 'edit', task })
  const closeForm = () => setFormModal(CLOSED_MODAL)

  return (
    <CCard>
      <CCardHeader className="d-flex justify-content-between align-items-start gap-2 flex-wrap">
        <div>
          <CButton
            color="link"
            className="p-0 mb-1 text-decoration-none"
            onClick={() => navigate('/admin/games')}
          >
            <CIcon icon={cilArrowLeft} className="me-1" />
            {t('tasks.backToGames')}
          </CButton>
          <h4 className="mb-1">{t('tasks.title')}</h4>
          <small className="text-medium-emphasis">{t('tasks.subtitle', { externalGameId })}</small>
        </div>
        <div className="d-flex gap-2 flex-wrap">
          <CButton color="secondary" variant="outline" onClick={() => setBulkOpen(true)}>
            <CIcon icon={cilLayers} className="me-1" />
            {t('tasks.bulkNew')}
          </CButton>
          <CButton color="primary" onClick={openCreate}>
            <CIcon icon={cilPlus} className="me-1" />
            {t('tasks.new')}
          </CButton>
        </div>
      </CCardHeader>
      <CCardBody>
        <div className="d-flex flex-wrap gap-2 align-items-end mb-3">
          <div style={{ minWidth: 240, flex: '1 1 240px' }}>
            <label className="form-label small text-medium-emphasis" htmlFor="tasks-search">
              {t('tasks.col.externalTaskId')}
            </label>
            <CFormInput
              id="tasks-search"
              type="search"
              placeholder={t('tasks.searchPlaceholder')}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>

        {error && <CAlert color="danger">{error}</CAlert>}

        {isLoading && <SkeletonTable columns={4} rows={6} hasActions />}

        {!isLoading && !error && tasks.length === 0 && (
          <CAlert color="info">{t('tasks.empty')}</CAlert>
        )}

        {!isLoading && tasks.length > 0 && filteredTasks.length === 0 && (
          <CAlert color="info">{t('common.noResults')}</CAlert>
        )}

        {!isLoading && filteredTasks.length > 0 && (
          <CTable hover responsive align="middle">
            <CTableHead>
              <CTableRow>
                <CTableHeaderCell>{t('tasks.col.externalTaskId')}</CTableHeaderCell>
                <CTableHeaderCell>{t('tasks.col.strategyId')}</CTableHeaderCell>
                <CTableHeaderCell>{t('tasks.col.params')}</CTableHeaderCell>
                <CTableHeaderCell>{t('tasks.col.createdAt')}</CTableHeaderCell>
                <CTableHeaderCell style={{ width: 120 }} className="text-end">
                  {t('tasks.col.actions')}
                </CTableHeaderCell>
              </CTableRow>
            </CTableHead>
            <CTableBody>
              {filteredTasks.map((task) => {
                const stratId = strategyIdOf(task)
                const paramCount = (task.taskParams || []).length
                return (
                  <CTableRow key={task.id}>
                    <CTableDataCell>
                      <code>{task.externalTaskId}</code>
                    </CTableDataCell>
                    <CTableDataCell>
                      {stratId ? (
                        <code>{stratId}</code>
                      ) : (
                        <span className="text-medium-emphasis">—</span>
                      )}
                    </CTableDataCell>
                    <CTableDataCell>
                      <span className="text-medium-emphasis">{paramCount}</span>
                    </CTableDataCell>
                    <CTableDataCell>
                      <span className="text-medium-emphasis small">
                        {formatDate(task.created_at)}
                      </span>
                    </CTableDataCell>
                    <CTableDataCell className="text-end">
                      <CDropdown variant="btn-group" alignment="end">
                        <CDropdownToggle size="sm" color="secondary" variant="outline">
                          {t('actions.rowActions')}
                        </CDropdownToggle>
                        <CDropdownMenu>
                          <CDropdownItem component="button" onClick={() => openEdit(task)}>
                            {t('actions.edit')}
                          </CDropdownItem>
                          <CDropdownItem
                            component="button"
                            onClick={() => setDuplicateTarget(task)}
                          >
                            {t('actions.duplicate')}
                          </CDropdownItem>
                          <CDropdownDivider />
                          <CDropdownItem
                            component="button"
                            className="text-danger"
                            onClick={() => setDeleteTarget(task)}
                          >
                            {t('actions.delete')}
                          </CDropdownItem>
                        </CDropdownMenu>
                      </CDropdown>
                    </CTableDataCell>
                  </CTableRow>
                )
              })}
            </CTableBody>
          </CTable>
        )}
      </CCardBody>

      {formModal.mode && (
        <TaskFormModal
          visible={!!formModal.mode}
          mode={formModal.mode}
          gameId={gameId}
          task={formModal.task}
          onClose={closeForm}
          onSaved={bumpRefresh}
        />
      )}

      {bulkOpen && (
        <TaskBulkModal
          visible={bulkOpen}
          gameId={gameId}
          onClose={() => setBulkOpen(false)}
          onCreated={bumpRefresh}
        />
      )}

      {duplicateTarget && (
        <TaskDuplicateModal
          visible={!!duplicateTarget}
          gameId={gameId}
          task={duplicateTarget}
          onClose={() => setDuplicateTarget(null)}
          onDuplicated={bumpRefresh}
        />
      )}

      {deleteTarget && (
        <TaskDeleteDialog
          visible={!!deleteTarget}
          gameId={gameId}
          task={deleteTarget}
          onCancel={() => setDeleteTarget(null)}
          onDeleted={() => {
            setDeleteTarget(null)
            bumpRefresh()
          }}
        />
      )}
    </CCard>
  )
}

export default GameTasksView
