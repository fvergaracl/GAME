// Read-only Users explorer.
//
// Users aren't a real CRUD entity in GAME: rows are created implicitly the
// first time points/actions land for an externalUserId, so there's nothing to
// create/edit/delete here. This view is therefore a lookup tool - type an
// externalUserId, see that user's points (grouped by game/task) and wallet
// (balances + transaction history).
//
// Both reads are independent endpoints (getUserPoints, getUserWallet) so we
// fan them out with Promise.allSettled: an existing user with no points still
// has a wallet, and a brand-new user may have neither. The "not found" state
// is only shown when BOTH endpoints 404 - that's the signal the externalUserId
// doesn't exist at all (each endpoint raises NotFoundError for unknown users).
//
// No mutations live here yet; the layout leaves room for a future "convert
// points" action (the backend already exposes /convert) without restructuring.

import React, { useState } from 'react'
import PropTypes from 'prop-types'
import { useTranslation } from 'react-i18next'
import {
  CAlert,
  CBadge,
  CButton,
  CCard,
  CCardBody,
  CCardHeader,
  CCol,
  CForm,
  CFormInput,
  CInputGroup,
  CRow,
  CTable,
  CTableBody,
  CTableDataCell,
  CTableHead,
  CTableHeaderCell,
  CTableRow,
} from '@coreui/react'
import CIcon from '@coreui/icons-react'
import { cilMoney, cilSearch, cilStar, cilWallet } from '@coreui/icons'

import { getUserPoints, getUserWallet } from '../../../api'
import { extractError } from '../../../utils/errors'
import { formatDateTime } from '../../../utils/date'
import { SkeletonText } from '../../../components/Skeleton'

const is404 = (err) => err?.response?.status === 404

// Points are integers; coins are floats with a small magnitude - show up to
// two decimals but drop trailing zeros so "12.00" reads as "12".
const formatNumber = (value) => {
  const n = Number(value)
  if (!Number.isFinite(n)) return '-'
  return n.toLocaleString(undefined, { maximumFractionDigits: 2 })
}

// Flatten List[AllPointsByGame] into table rows + a grand total. The backend
// already filters each task's ``points`` array down to the queried user, but
// we re-check externalUserId defensively so a future shared payload can't leak
// another user's totals into this table.
const flattenPoints = (games, externalUserId) => {
  const rows = []
  let total = 0
  for (const game of games || []) {
    for (const task of game?.task || []) {
      for (const entry of task?.points || []) {
        if (externalUserId && entry.externalUserId && entry.externalUserId !== externalUserId) {
          continue
        }
        const points = Number(entry?.points) || 0
        total += points
        rows.push({
          key: `${game.externalGameId}::${task.externalTaskId}::${entry.externalUserId}`,
          externalGameId: game.externalGameId,
          externalTaskId: task.externalTaskId,
          points,
          timesAwarded: Number(entry?.timesAwarded) || 0,
        })
      }
    }
  }
  return { rows, total }
}

// Small icon + value + label stat card. Kept local to this view - the
// dashboard's WidgetKpi is chart-driven and a poor fit for a single scalar.
const StatCard = ({ icon, label, value, hint }) => (
  <CCard className="h-100">
    <CCardBody className="d-flex align-items-center gap-3">
      <CIcon icon={icon} size="xl" className="text-medium-emphasis flex-shrink-0" />
      <div style={{ minWidth: 0 }}>
        <div className="fs-5 fw-semibold text-truncate">{value}</div>
        <div className="small text-medium-emphasis">{label}</div>
        {hint && <div className="small text-medium-emphasis">{hint}</div>}
      </div>
    </CCardBody>
  </CCard>
)

StatCard.propTypes = {
  icon: PropTypes.oneOfType([PropTypes.array, PropTypes.string]).isRequired,
  label: PropTypes.node.isRequired,
  value: PropTypes.node.isRequired,
  hint: PropTypes.node,
}

const UsersExplorerView = () => {
  const { t } = useTranslation('management')

  const [input, setInput] = useState('')
  // The externalUserId that the currently displayed result belongs to. Held
  // separately from ``input`` so editing the box after a search doesn't
  // relabel the results until the next submit.
  const [queried, setQueried] = useState(null)

  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [notFound, setNotFound] = useState(false)
  const [points, setPoints] = useState([])
  const [wallet, setWallet] = useState(null)

  const runSearch = async (e) => {
    e?.preventDefault?.()
    const externalUserId = input.trim()
    if (!externalUserId || isLoading) return

    setIsLoading(true)
    setError(null)
    setNotFound(false)
    setQueried(externalUserId)

    const [pointsResult, walletResult] = await Promise.allSettled([
      getUserPoints(externalUserId),
      getUserWallet(externalUserId),
    ])

    const pointsOk = pointsResult.status === 'fulfilled'
    const walletOk = walletResult.status === 'fulfilled'

    if (!pointsOk && !walletOk) {
      // Both reads failed. If they're both 404 the user simply doesn't
      // exist; anything else is a real error worth surfacing verbatim.
      if (is404(pointsResult.reason) && is404(walletResult.reason)) {
        setNotFound(true)
        setPoints([])
        setWallet(null)
      } else {
        const reason = is404(pointsResult.reason) ? walletResult.reason : pointsResult.reason
        setError(extractError(reason, t('users.loadError')))
        setPoints([])
        setWallet(null)
      }
    } else {
      // At least one read succeeded → the user exists. Render whatever we
      // got; a 404 on one side just means "no points" or "no wallet".
      setPoints(pointsOk ? pointsResult.value || [] : [])
      setWallet(walletOk ? walletResult.value || null : null)
    }

    setIsLoading(false)
  }

  const { rows: pointRows, total: totalPoints } = flattenPoints(points, queried)
  const balances = wallet?.wallet || null
  const transactions = wallet?.walletTransactions || []
  const hasResult = !isLoading && !error && !notFound && queried !== null

  return (
    <CCard>
      <CCardHeader>
        <h4 className="mb-1">{t('users.title')}</h4>
        <small className="text-medium-emphasis">{t('users.subtitle')}</small>
      </CCardHeader>
      <CCardBody>
        <CForm onSubmit={runSearch} className="mb-4" role="search">
          <label className="form-label small text-medium-emphasis" htmlFor="users-search">
            {t('users.searchLabel')}
          </label>
          <CInputGroup style={{ maxWidth: 520 }}>
            <CFormInput
              id="users-search"
              type="search"
              autoComplete="off"
              placeholder={t('users.searchPlaceholder')}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isLoading}
            />
            <CButton type="submit" color="primary" disabled={isLoading || !input.trim()}>
              <CIcon icon={cilSearch} className="me-1" />
              {isLoading ? t('users.searching') : t('users.search')}
            </CButton>
          </CInputGroup>
        </CForm>

        {error && <CAlert color="danger">{error}</CAlert>}

        {notFound && (
          <CAlert color="warning">{t('users.notFound', { externalUserId: queried })}</CAlert>
        )}

        {queried === null && !isLoading && <CAlert color="info">{t('users.empty')}</CAlert>}

        {isLoading && (
          <div className="py-2">
            <SkeletonText lines={4} />
          </div>
        )}

        {hasResult && (
          <>
            <div className="d-flex align-items-baseline gap-2 mb-3 flex-wrap">
              <code className="fs-6">{queried}</code>
              {wallet?.userId && (
                <span className="small text-medium-emphasis">
                  {t('users.internalId')}: <code>{wallet.userId}</code>
                </span>
              )}
            </div>

            <CRow className="g-3 mb-4">
              <CCol xs={12} sm={6} xl={3}>
                <StatCard
                  icon={cilStar}
                  label={t('users.summary.totalPoints')}
                  value={formatNumber(totalPoints)}
                />
              </CCol>
              <CCol xs={12} sm={6} xl={3}>
                <StatCard
                  icon={cilStar}
                  label={t('users.summary.pointsBalance')}
                  value={balances ? formatNumber(balances.pointsBalance) : '-'}
                />
              </CCol>
              <CCol xs={12} sm={6} xl={3}>
                <StatCard
                  icon={cilMoney}
                  label={t('users.summary.coinsBalance')}
                  value={balances ? formatNumber(balances.coinsBalance) : '-'}
                />
              </CCol>
              <CCol xs={12} sm={6} xl={3}>
                <StatCard
                  icon={cilWallet}
                  label={t('users.summary.conversionRate')}
                  value={balances ? formatNumber(balances.conversionRate) : '-'}
                  hint={
                    balances && Number(balances.conversionRate) > 0
                      ? t('users.summary.conversionRateHelp', {
                          rate: formatNumber(balances.conversionRate),
                        })
                      : null
                  }
                />
              </CCol>
            </CRow>

            <h5 className="mb-2">{t('users.points.title')}</h5>
            {pointRows.length === 0 ? (
              <CAlert color="info">{t('users.points.empty')}</CAlert>
            ) : (
              <CTable hover responsive align="middle" className="mb-4">
                <CTableHead>
                  <CTableRow>
                    <CTableHeaderCell>{t('users.points.game')}</CTableHeaderCell>
                    <CTableHeaderCell>{t('users.points.task')}</CTableHeaderCell>
                    <CTableHeaderCell className="text-end">
                      {t('users.points.points')}
                    </CTableHeaderCell>
                    <CTableHeaderCell className="text-end">
                      {t('users.points.timesAwarded')}
                    </CTableHeaderCell>
                  </CTableRow>
                </CTableHead>
                <CTableBody>
                  {pointRows.map((row) => (
                    <CTableRow key={row.key}>
                      <CTableDataCell>
                        <code>{row.externalGameId}</code>
                      </CTableDataCell>
                      <CTableDataCell>
                        <code>{row.externalTaskId}</code>
                      </CTableDataCell>
                      <CTableDataCell className="text-end">
                        {formatNumber(row.points)}
                      </CTableDataCell>
                      <CTableDataCell className="text-end text-medium-emphasis">
                        {formatNumber(row.timesAwarded)}
                      </CTableDataCell>
                    </CTableRow>
                  ))}
                </CTableBody>
              </CTable>
            )}

            <h5 className="mb-2">{t('users.wallet.transactions')}</h5>
            {!balances ? (
              <CAlert color="info">{t('users.wallet.noWallet')}</CAlert>
            ) : transactions.length === 0 ? (
              <CAlert color="info">{t('users.wallet.noTransactions')}</CAlert>
            ) : (
              <CTable hover responsive align="middle">
                <CTableHead>
                  <CTableRow>
                    <CTableHeaderCell>{t('users.wallet.col.date')}</CTableHeaderCell>
                    <CTableHeaderCell>{t('users.wallet.col.type')}</CTableHeaderCell>
                    <CTableHeaderCell className="text-end">
                      {t('users.wallet.col.points')}
                    </CTableHeaderCell>
                    <CTableHeaderCell className="text-end">
                      {t('users.wallet.col.coins')}
                    </CTableHeaderCell>
                  </CTableRow>
                </CTableHead>
                <CTableBody>
                  {transactions.map((tx) => (
                    <CTableRow key={tx.id}>
                      <CTableDataCell>
                        <span className="text-medium-emphasis small">
                          {formatDateTime(tx.created_at)}
                        </span>
                      </CTableDataCell>
                      <CTableDataCell>
                        <CBadge color="secondary">{tx.transactionType}</CBadge>
                      </CTableDataCell>
                      <CTableDataCell className="text-end">{formatNumber(tx.points)}</CTableDataCell>
                      <CTableDataCell className="text-end">{formatNumber(tx.coins)}</CTableDataCell>
                    </CTableRow>
                  ))}
                </CTableBody>
              </CTable>
            )}
          </>
        )}
      </CCardBody>
    </CCard>
  )
}

export default UsersExplorerView
