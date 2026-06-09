import React, { useState } from 'react'
import {
  CAlert,
  CButton,
  CCard,
  CCardBody,
  CCardHeader,
  CCol,
  CForm,
  CFormCheck,
  CFormInput,
  CFormLabel,
  CFormSelect,
  CRow,
  CSpinner,
} from '@coreui/react'
import { downloadExport } from '../../api'
import { extractError } from '../../utils/errors'

const DATASETS = [
  { value: 'users', label: 'Users' },
  { value: 'user-points', label: 'User points' },
  { value: 'user-interactions', label: 'User interactions' },
  { value: 'wallet-transactions', label: 'Wallet transactions' },
]

const FORMATS = [
  { value: 'csv', label: 'CSV' },
  { value: 'xlsx', label: 'Excel (XLSX)' },
  { value: 'json', label: 'JSON' },
]

// Datasets that accept externalGameId / externalTaskId filters server-side.
// For users + wallet-transactions those params are ignored, so we hide the
// inputs entirely to avoid implying they do something.
const DATASETS_WITH_GAME_TASK_FILTERS = new Set(['user-points'])

const HARD_LIMIT = 100000

const ExportData = () => {
  const [dataset, setDataset] = useState('users')
  const [format, setFormat] = useState('csv')
  const [externalGameId, setExternalGameId] = useState('')
  const [externalTaskId, setExternalTaskId] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [limit, setLimit] = useState(10000)
  const [isDownloading, setIsDownloading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

  const showGameTaskFilters = DATASETS_WITH_GAME_TASK_FILTERS.has(dataset)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)

    const parsedLimit = Number(limit)
    if (!Number.isInteger(parsedLimit) || parsedLimit < 1 || parsedLimit > HARD_LIMIT) {
      setError(`Limit must be an integer between 1 and ${HARD_LIMIT.toLocaleString()}.`)
      return
    }
    if (dateFrom && dateTo && new Date(dateFrom) > new Date(dateTo)) {
      setError('"Date from" must be before "Date to".')
      return
    }

    setIsDownloading(true)
    try {
      const result = await downloadExport({
        dataset,
        format,
        externalGameId: showGameTaskFilters ? externalGameId || null : null,
        externalTaskId: showGameTaskFilters ? externalTaskId || null : null,
        dateFrom: dateFrom || null,
        dateTo: dateTo || null,
        limit: parsedLimit,
      })
      setSuccess(`Downloaded ${result.filename} (${formatBytes(result.size)}).`)
    } catch (err) {
      setError(extractDownloadError(err))
    } finally {
      setIsDownloading(false)
    }
  }

  return (
    <CRow>
      <CCol xs={12}>
        <CCard className="mb-4">
          <CCardHeader>
            <strong>Data export</strong>{' '}
            <small className="text-body-secondary">Download a dataset</small>
          </CCardHeader>
          <CCardBody>
            <p className="text-body-secondary small">
              Pick a dataset, format and optional filters. The download starts in your browser as
              soon as the server is ready - no email, no background job. Each request is recorded in{' '}
              <em>Export history</em>.
            </p>

            <CForm onSubmit={handleSubmit}>
              <CRow className="mb-3">
                <CFormLabel htmlFor="dataset" className="col-sm-2 col-form-label">
                  Dataset
                </CFormLabel>
                <CCol sm={10}>
                  <CFormSelect
                    id="dataset"
                    value={dataset}
                    onChange={(e) => setDataset(e.target.value)}
                  >
                    {DATASETS.map((ds) => (
                      <option key={ds.value} value={ds.value}>
                        {ds.label}
                      </option>
                    ))}
                  </CFormSelect>
                </CCol>
              </CRow>

              <CRow className="mb-3">
                <CFormLabel className="col-sm-2 col-form-label">Format</CFormLabel>
                <CCol sm={10}>
                  {FORMATS.map((f) => (
                    <CFormCheck
                      inline
                      key={f.value}
                      type="radio"
                      id={`format-${f.value}`}
                      name="format"
                      label={f.label}
                      value={f.value}
                      checked={format === f.value}
                      onChange={(e) => setFormat(e.target.value)}
                    />
                  ))}
                </CCol>
              </CRow>

              {showGameTaskFilters && (
                <>
                  <CRow className="mb-3">
                    <CFormLabel htmlFor="externalGameId" className="col-sm-2 col-form-label">
                      Game ID
                    </CFormLabel>
                    <CCol sm={10}>
                      <CFormInput
                        id="externalGameId"
                        type="text"
                        placeholder="externalGameId (optional)"
                        value={externalGameId}
                        onChange={(e) => setExternalGameId(e.target.value)}
                      />
                    </CCol>
                  </CRow>
                  <CRow className="mb-3">
                    <CFormLabel htmlFor="externalTaskId" className="col-sm-2 col-form-label">
                      Task ID
                    </CFormLabel>
                    <CCol sm={10}>
                      <CFormInput
                        id="externalTaskId"
                        type="text"
                        placeholder="externalTaskId (optional)"
                        value={externalTaskId}
                        onChange={(e) => setExternalTaskId(e.target.value)}
                      />
                    </CCol>
                  </CRow>
                </>
              )}

              <CRow className="mb-3">
                <CFormLabel htmlFor="dateFrom" className="col-sm-2 col-form-label">
                  Date from
                </CFormLabel>
                <CCol sm={4}>
                  <CFormInput
                    id="dateFrom"
                    type="datetime-local"
                    value={dateFrom}
                    onChange={(e) => setDateFrom(e.target.value)}
                  />
                </CCol>
                <CFormLabel htmlFor="dateTo" className="col-sm-2 col-form-label">
                  Date to
                </CFormLabel>
                <CCol sm={4}>
                  <CFormInput
                    id="dateTo"
                    type="datetime-local"
                    value={dateTo}
                    onChange={(e) => setDateTo(e.target.value)}
                  />
                </CCol>
              </CRow>

              <CRow className="mb-3">
                <CFormLabel htmlFor="limit" className="col-sm-2 col-form-label">
                  Limit
                </CFormLabel>
                <CCol sm={10}>
                  <CFormInput
                    id="limit"
                    type="number"
                    min={1}
                    max={HARD_LIMIT}
                    value={limit}
                    onChange={(e) => setLimit(e.target.value)}
                  />
                  <small className="text-body-secondary">
                    Hard cap: {HARD_LIMIT.toLocaleString()} rows per request.
                  </small>
                </CCol>
              </CRow>

              <div className="text-center">
                <CButton color="primary" type="submit" disabled={isDownloading}>
                  {isDownloading ? (
                    <>
                      <CSpinner size="sm" className="me-2" /> Preparing download…
                    </>
                  ) : (
                    'Download'
                  )}
                </CButton>
              </div>
            </CForm>

            {error && (
              <CAlert color="danger" className="mt-4">
                {error}
              </CAlert>
            )}
            {success && (
              <CAlert color="success" className="mt-4">
                {success}
              </CAlert>
            )}
          </CCardBody>
        </CCard>
      </CCol>
    </CRow>
  )
}

function formatBytes(bytes) {
  if (!bytes && bytes !== 0) return '?'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

// Sprint 9: download-specific wrapper around the shared extractError.
// Carries the dataset-specific 403 and 422 messages that the generic
// helper doesn't know about; everything else (Blob bodies, generic
// fallback, network errors) routes through the shared helper.
function extractDownloadError(err) {
  if (err?.response?.status === 422) {
    return 'Invalid parameters. Check the date range, limit, and format.'
  }
  return extractError(err, {
    fallback: 'Network error',
    forbidden: 'Forbidden. You need the AdministratorGAME role to download data.',
  })
}

export default ExportData
