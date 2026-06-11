// Games management view.
//
// The admin's home for the game lifecycle: a server-paginated, searchable
// table of games with create + edit and delete + duplicate.
// "Ver tareas" and the per-row actions dropdown
// is the seam each action plugs into.
//
// Reuses the StrategyAssignmentsView shape (server pagination + debounced
// search via listGames) but stays read-light: no row expansion, no
// multi-select. Mutations live in dedicated modals (GameFormModal,
// GameDuplicateModal) and a shared ConfirmDialog (GameDeleteDialog); this
// view only lists and bumps refreshTick to reload after any of them saves.

import React, { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
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
  CFormSelect,
  CTable,
  CTableBody,
  CTableDataCell,
  CTableHead,
  CTableHeaderCell,
  CTableRow,
} from '@coreui/react'
import CIcon from '@coreui/icons-react'
import { cilPlus } from '@coreui/icons'

import { listGames } from '../../../api'
import { extractError } from '../../../utils/errors'
import { formatDateTime } from '../../../utils/date'
import { SkeletonTable } from '../../../components/Skeleton'
import GameFormModal, { PLATFORM_PRESETS } from './GameFormModal'
import GameDeleteDialog from './GameDeleteDialog'
import GameDuplicateModal from './GameDuplicateModal'

const PAGE_SIZE_OPTIONS = [10, 20, 50]

// Closed when ``mode`` is null; create/edit drive GameFormModal.
const CLOSED_MODAL = { mode: null, gameId: null }

const GamesManagementView = () => {
  const { t } = useTranslation('management')
  const navigate = useNavigate()

  const [games, setGames] = useState([])
  const [totalCount, setTotalCount] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [platformFilter, setPlatformFilter] = useState('')

  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  // Bumped after a successful save to force a reload of the current page.
  const [refreshTick, setRefreshTick] = useState(0)

  const [modal, setModal] = useState(CLOSED_MODAL)
  // Delete/duplicate each target a single row; we hold the whole game object
  // (not just the id) so the dialogs can show externalGameId without a refetch.
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [duplicateTarget, setDuplicateTarget] = useState(null)

  // Debounce the search box so typing doesn't fire a request per keystroke.
  useEffect(() => {
    const handle = setTimeout(() => {
      setSearch(searchInput.trim())
      setPage(1)
    }, 300)
    return () => clearTimeout(handle)
  }, [searchInput])

  const reload = useCallback(() => {
    let cancelled = false
    setIsLoading(true)
    setError(null)
    listGames({
      page,
      pageSize,
      externalGameId: search || undefined,
      platform: platformFilter || undefined,
    })
      .then((result) => {
        if (cancelled) return
        setGames(result?.items || [])
        setTotalCount(result?.search_options?.total_count || 0)
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
  }, [page, pageSize, search, platformFilter, t])

  useEffect(() => {
    const cleanup = reload()
    return cleanup
  }, [reload, refreshTick])

  const totalPages = Math.max(1, Math.ceil(totalCount / pageSize))
  const hasFilters = !!search || !!platformFilter

  const openCreate = () => setModal({ mode: 'create', gameId: null })
  const openEdit = (game) => setModal({ mode: 'edit', gameId: String(game.gameId) })
  const closeModal = () => setModal(CLOSED_MODAL)

  return (
    <CCard>
      <CCardHeader className="d-flex justify-content-between align-items-start gap-2 flex-wrap">
        <div>
          <h4 className="mb-1">{t('games.title')}</h4>
          <small className="text-medium-emphasis">{t('games.subtitle')}</small>
        </div>
        <CButton color="primary" onClick={openCreate}>
          <CIcon icon={cilPlus} className="me-1" />
          {t('games.new')}
        </CButton>
      </CCardHeader>
      <CCardBody>
        <div className="d-flex flex-wrap gap-2 align-items-end mb-3">
          <div style={{ minWidth: 240, flex: '1 1 240px' }}>
            <label className="form-label small text-medium-emphasis" htmlFor="games-search">
              {t('games.col.externalGameId')}
            </label>
            <CFormInput
              id="games-search"
              type="search"
              placeholder={t('games.searchPlaceholder')}
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
            />
          </div>
          <div style={{ width: 200 }}>
            <label className="form-label small text-medium-emphasis" htmlFor="games-platform">
              {t('games.col.platform')}
            </label>
            <CFormSelect
              id="games-platform"
              value={platformFilter}
              onChange={(e) => {
                setPlatformFilter(e.target.value)
                setPage(1)
              }}
            >
              <option value="">{t('games.platformAll')}</option>
              {PLATFORM_PRESETS.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </CFormSelect>
          </div>
          <div style={{ width: 130 }}>
            <label className="form-label small text-medium-emphasis" htmlFor="games-page-size">
              {t('common:pagination.perPage')}
            </label>
            <CFormSelect
              id="games-page-size"
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

        {isLoading && <SkeletonTable columns={4} rows={pageSize > 10 ? 8 : pageSize} hasActions />}

        {!isLoading && !error && totalCount === 0 && (
          <CAlert color="info">{hasFilters ? t('games.emptySearch') : t('games.empty')}</CAlert>
        )}

        {!isLoading && games.length > 0 && (
          <>
            <CTable hover responsive align="middle">
              <CTableHead>
                <CTableRow>
                  <CTableHeaderCell>{t('games.col.externalGameId')}</CTableHeaderCell>
                  <CTableHeaderCell>{t('games.col.platform')}</CTableHeaderCell>
                  <CTableHeaderCell>{t('games.col.strategyId')}</CTableHeaderCell>
                  <CTableHeaderCell>{t('games.col.createdAt')}</CTableHeaderCell>
                  <CTableHeaderCell style={{ width: 120 }} className="text-end">
                    {t('games.col.actions')}
                  </CTableHeaderCell>
                </CTableRow>
              </CTableHead>
              <CTableBody>
                {games.map((game) => (
                  <CTableRow key={game.gameId}>
                    <CTableDataCell>
                      <code>{game.externalGameId}</code>
                    </CTableDataCell>
                    <CTableDataCell>{game.platform || '-'}</CTableDataCell>
                    <CTableDataCell>
                      {game.strategyId ? (
                        <code>{game.strategyId}</code>
                      ) : (
                        <span className="text-medium-emphasis">-</span>
                      )}
                    </CTableDataCell>
                    <CTableDataCell>
                      <span className="text-medium-emphasis small">
                        {formatDateTime(game.created_at)}
                      </span>
                    </CTableDataCell>
                    <CTableDataCell className="text-end">
                      <CDropdown variant="btn-group" alignment="end" portal>
                        <CDropdownToggle size="sm" color="secondary" variant="outline">
                          {t('actions.rowActions')}
                        </CDropdownToggle>
                        <CDropdownMenu>
                          <CDropdownItem
                            component="button"
                            onClick={() => navigate(`/admin/games/${game.gameId}/tasks`)}
                          >
                            {t('actions.viewTasks')}
                          </CDropdownItem>
                          <CDropdownDivider />
                          <CDropdownItem component="button" onClick={() => openEdit(game)}>
                            {t('actions.edit')}
                          </CDropdownItem>
                          <CDropdownItem
                            component="button"
                            onClick={() => setDuplicateTarget(game)}
                          >
                            {t('actions.duplicate')}
                          </CDropdownItem>
                          <CDropdownDivider />
                          <CDropdownItem
                            component="button"
                            className="text-danger"
                            onClick={() => setDeleteTarget(game)}
                          >
                            {t('actions.delete')}
                          </CDropdownItem>
                        </CDropdownMenu>
                      </CDropdown>
                    </CTableDataCell>
                  </CTableRow>
                ))}
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
                {t('common:pagination.previous')}
              </CButton>
              <span className="text-medium-emphasis small">
                {t('common:pagination.page', { page, total: totalPages })}
              </span>
              <CButton
                color="secondary"
                variant="outline"
                size="sm"
                disabled={page >= totalPages || isLoading}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              >
                {t('common:pagination.next')}
              </CButton>
            </div>
          </>
        )}
      </CCardBody>

      {modal.mode && (
        <GameFormModal
          visible={!!modal.mode}
          mode={modal.mode}
          gameId={modal.gameId}
          onClose={closeModal}
          onSaved={() => setRefreshTick((n) => n + 1)}
        />
      )}

      {duplicateTarget && (
        <GameDuplicateModal
          visible={!!duplicateTarget}
          game={duplicateTarget}
          onClose={() => setDuplicateTarget(null)}
          onDuplicated={() => setRefreshTick((n) => n + 1)}
        />
      )}

      {deleteTarget && (
        <GameDeleteDialog
          visible={!!deleteTarget}
          game={deleteTarget}
          onCancel={() => setDeleteTarget(null)}
          onDeleted={() => {
            setDeleteTarget(null)
            setRefreshTick((n) => n + 1)
          }}
        />
      )}
    </CCard>
  )
}

export default GamesManagementView
