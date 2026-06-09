import React, { useCallback, useEffect, useState } from 'react'
import {
  CAlert,
  CBadge,
  CButton,
  CButtonGroup,
  CCard,
  CCardBody,
  CCardHeader,
  CCol,
  CRow,
  CSpinner,
  CTable,
  CTableBody,
  CTableDataCell,
  CTableHead,
  CTableHeaderCell,
  CTableRow,
} from '@coreui/react'
import { getExportHistory } from '../../api'
import { extractError } from '../../utils/errors'
import { SkeletonTable } from '../../components/Skeleton'

const STATUS_COLORS = {
  completed: 'success',
  started: 'info',
  failed: 'danger',
}

const ExportHistory = () => {
  const [scope, setScope] = useState('mine')
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchHistory = useCallback(async (nextScope) => {
    setLoading(true)
    setError(null)
    try {
      const data = await getExportHistory({ scope: nextScope, limit: 100 })
      setRows(Array.isArray(data) ? data : [])
    } catch (err) {
      setError(
        extractError(err, {
          fallback: 'Network error',
          forbidden: 'Forbidden. You need the AdministratorGAME role.',
        }),
      )
      setRows([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchHistory(scope)
  }, [scope, fetchHistory])

  return (
    <CRow>
      <CCol xs={12}>
        <CCard className="mb-4">
          <CCardHeader className="d-flex justify-content-between align-items-center">
            <div>
              <strong>Export history</strong>{' '}
              <small className="text-body-secondary">Recent download requests</small>
            </div>
            <div className="d-flex align-items-center gap-2">
              <CButtonGroup role="group" aria-label="History scope">
                <CButton
                  color={scope === 'mine' ? 'primary' : 'secondary'}
                  variant={scope === 'mine' ? undefined : 'outline'}
                  size="sm"
                  onClick={() => setScope('mine')}
                >
                  Mine
                </CButton>
                <CButton
                  color={scope === 'all' ? 'primary' : 'secondary'}
                  variant={scope === 'all' ? undefined : 'outline'}
                  size="sm"
                  onClick={() => setScope('all')}
                >
                  All admins
                </CButton>
              </CButtonGroup>
              <CButton
                color="secondary"
                variant="outline"
                size="sm"
                onClick={() => fetchHistory(scope)}
                disabled={loading}
              >
                {loading ? <CSpinner size="sm" /> : 'Refresh'}
              </CButton>
            </div>
          </CCardHeader>
          <CCardBody>
            {error && <CAlert color="danger">{error}</CAlert>}

            {loading && rows.length === 0 && (
              // Skeleton instead of an empty card. Columns
              // match the real table so the swap is jump-free.
              <SkeletonTable columns={8} rows={4} />
            )}

            {!error && rows.length === 0 && !loading && (
              <p className="text-body-secondary mb-0">
                No exports recorded yet. Once you download a dataset from the
                <em> Data export</em> page it will show up here.
              </p>
            )}

            {rows.length > 0 && (
              <CTable hover responsive small>
                <CTableHead>
                  <CTableRow>
                    <CTableHeaderCell scope="col">When</CTableHeaderCell>
                    <CTableHeaderCell scope="col">Dataset</CTableHeaderCell>
                    <CTableHeaderCell scope="col">Format</CTableHeaderCell>
                    <CTableHeaderCell scope="col">Status</CTableHeaderCell>
                    <CTableHeaderCell scope="col" className="text-end">
                      Rows
                    </CTableHeaderCell>
                    <CTableHeaderCell scope="col" className="text-end">
                      Limit
                    </CTableHeaderCell>
                    <CTableHeaderCell scope="col">By</CTableHeaderCell>
                    <CTableHeaderCell scope="col">Filters</CTableHeaderCell>
                  </CTableRow>
                </CTableHead>
                <CTableBody>
                  {rows.map((row) => (
                    <CTableRow key={row.id}>
                      <CTableDataCell>{formatTimestamp(row.created_at)}</CTableDataCell>
                      <CTableDataCell>{row.datasetType}</CTableDataCell>
                      <CTableDataCell>{row.format}</CTableDataCell>
                      <CTableDataCell>
                        <CBadge color={STATUS_COLORS[row.status] || 'secondary'}>
                          {row.status}
                        </CBadge>
                      </CTableDataCell>
                      <CTableDataCell className="text-end">
                        {row.rowCount >= 0 ? row.rowCount : '-'}
                      </CTableDataCell>
                      <CTableDataCell className="text-end">{row.rowLimit}</CTableDataCell>
                      <CTableDataCell>
                        <span className="text-truncate d-inline-block" style={{ maxWidth: 180 }}>
                          {row.requestedBy || '-'}
                        </span>
                      </CTableDataCell>
                      <CTableDataCell>
                        <code className="small">{summarizeFilters(row.filters)}</code>
                      </CTableDataCell>
                    </CTableRow>
                  ))}
                </CTableBody>
              </CTable>
            )}
          </CCardBody>
        </CCard>
      </CCol>
    </CRow>
  )
}

function formatTimestamp(value) {
  if (!value) return '-'
  try {
    return new Date(value).toLocaleString()
  } catch {
    return value
  }
}

function summarizeFilters(filters) {
  if (!filters || typeof filters !== 'object') return '{}'
  const entries = Object.entries(filters)
  if (entries.length === 0) return '{}'
  return entries.map(([k, v]) => `${k}=${typeof v === 'object' ? JSON.stringify(v) : v}`).join(', ')
}

export default ExportHistory
