// Sprint 10 — Strategy observability view.
//
// Surfaces metrics the backend already collects via DslExecutionObserver
// (status mix, latency percentiles, top errors, case-name breakdown,
// points distribution). The page is read-only: a single fetch per
// strategy + window pair drives every card, so the network footprint
// stays predictable even at scale.
//
// Picker design: a plain CFormSelect listing every strategy in the
// realm. Bigger UX (search, sort by error rate, "compare against this
// one" CTA) lives a click away in the A/B comparison view — this page
// is the "what is happening with strategy X" surface.

import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
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
  CFormSelect,
  CProgress,
  CProgressStacked,
  CRow,
  CTable,
  CTableBody,
  CTableDataCell,
  CTableHead,
  CTableHeaderCell,
  CTableRow,
} from '@coreui/react'

import { getStrategyMetrics, listCustomStrategies } from '../../api'
import { extractError } from '../../utils/errors'
import { SkeletonCard } from '../../components/Skeleton'

// Window options — fixed presets cover the realistic ranges. A custom
// date-range picker would be overkill for now (the underlying data is
// downsampled at 5% so multi-day windows are common anyway).
const WINDOW_OPTIONS = ['all', '24h', '7d', '30d']

const windowToSinceIso = (key) => {
  if (!key || key === 'all') return undefined
  const ms =
    key === '24h' ? 24 * 3600 * 1000 : key === '7d' ? 7 * 86400 * 1000 : 30 * 86400 * 1000
  return new Date(Date.now() - ms).toISOString()
}

const formatPct = (value) => `${(value * 100).toFixed(1)}%`
const formatMs = (value) => `${value.toFixed(1)} ms`
const formatNum = (value, digits = 0) =>
  Number.isFinite(value) ? value.toFixed(digits) : '—'

const STATUS_COLORS = {
  ok: 'success',
  error: 'danger',
  timeout: 'warning',
  limit: 'info',
  other: 'secondary',
}

// Reusable bar-style breakdown for the duration / points histograms.
// We render counts as proportions of the max bucket so a sparse
// histogram still reads as a shape, not a flat line.
function HistogramBars({ buckets, emptyLabel }) {
  const max = useMemo(() => buckets.reduce((m, b) => Math.max(m, b.count || 0), 0), [buckets])
  if (!buckets || buckets.length === 0 || max === 0) {
    return <p className="text-medium-emphasis mb-0">{emptyLabel}</p>
  }
  return (
    <div className="d-flex flex-column gap-1">
      {buckets.map((bucket, idx) => {
        const pct = max > 0 ? Math.max(2, Math.round((bucket.count / max) * 100)) : 0
        return (
          <div key={`${bucket.label}-${idx}`} className="d-flex align-items-center gap-2">
            <small style={{ minWidth: 90 }} className="text-medium-emphasis">
              {bucket.label}
            </small>
            <div className="flex-grow-1">
              <CProgress thin color="info" value={pct} />
            </div>
            <small style={{ minWidth: 50 }} className="text-end fw-semibold">
              {bucket.count}
            </small>
          </div>
        )
      })}
    </div>
  )
}

// One ratio chip — used in the status card to display ok / error /
// timeout percentages without a third-party chart dependency.
function StatChip({ color, label, value, sub }) {
  return (
    <div className="d-flex flex-column align-items-start">
      <CBadge color={color} className="mb-1">
        {label}
      </CBadge>
      <span className="fs-5 fw-semibold">{value}</span>
      {sub != null && <small className="text-medium-emphasis">{sub}</small>}
    </div>
  )
}

const StrategyObservabilityView = () => {
  const { t } = useTranslation('strategies')
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  const initialId = searchParams.get('id') || ''
  const initialWindow = searchParams.get('window') || 'all'

  const [strategies, setStrategies] = useState([])
  const [selectedId, setSelectedId] = useState(initialId)
  const [windowKey, setWindowKey] = useState(initialWindow)
  const [metrics, setMetrics] = useState(null)
  const [isLoadingList, setIsLoadingList] = useState(false)
  const [isLoadingMetrics, setIsLoadingMetrics] = useState(false)
  const [listError, setListError] = useState(null)
  const [metricsError, setMetricsError] = useState(null)

  // Sync URL state when the user picks a different strategy or window
  // so the page is shareable ("here's the latency view for strategy X
  // over the last 7 days"). We replace rather than push so the back
  // button still leaves the view rather than cycling selections.
  useEffect(() => {
    const next = new URLSearchParams()
    if (selectedId) next.set('id', selectedId)
    if (windowKey && windowKey !== 'all') next.set('window', windowKey)
    setSearchParams(next, { replace: true })
  }, [selectedId, windowKey, setSearchParams])

  useEffect(() => {
    let cancelled = false
    setIsLoadingList(true)
    setListError(null)
    listCustomStrategies({ limit: 500 })
      .then((rows) => {
        if (cancelled) return
        setStrategies(Array.isArray(rows) ? rows : [])
      })
      .catch((err) => {
        if (cancelled) return
        setListError(extractError(err, t('observability.errors.loadList')))
      })
      .finally(() => {
        if (!cancelled) setIsLoadingList(false)
      })
    return () => {
      cancelled = true
    }
  }, [t])

  const loadMetrics = useCallback(
    (id, key) => {
      if (!id) {
        setMetrics(null)
        return
      }
      let cancelled = false
      setIsLoadingMetrics(true)
      setMetricsError(null)
      getStrategyMetrics(id, { since: windowToSinceIso(key) })
        .then((data) => {
          if (cancelled) return
          setMetrics(data)
        })
        .catch((err) => {
          if (cancelled) return
          setMetricsError(extractError(err, t('observability.errors.load')))
          setMetrics(null)
        })
        .finally(() => {
          if (!cancelled) setIsLoadingMetrics(false)
        })
      return () => {
        cancelled = true
      }
    },
    [t],
  )

  useEffect(() => {
    const cleanup = loadMetrics(selectedId, windowKey)
    return cleanup
  }, [selectedId, windowKey, loadMetrics])

  const selectedStrategy = useMemo(
    () => strategies.find((s) => s.id === selectedId) || null,
    [strategies, selectedId],
  )

  const goCompare = () => {
    const target = selectedId ? `?a=${encodeURIComponent(selectedId)}` : ''
    navigate(`/strategies/compare${target}`)
  }

  // Stacked status bar — proportions for ok / error / timeout / limit.
  // CProgressStacked rejects 0-value children silently, so filter out
  // empties before mapping (otherwise the gaps render as wide separators).
  const statusBars = useMemo(() => {
    if (!metrics) return []
    const { statusBreakdown: sb } = metrics
    if (!sb.total) return []
    return [
      { key: 'ok', label: t('observability.labels.ok'), color: 'success', count: sb.ok },
      { key: 'error', label: t('observability.labels.error'), color: 'danger', count: sb.error },
      {
        key: 'timeout',
        label: t('observability.labels.timeout'),
        color: 'warning',
        count: sb.timeout,
      },
      { key: 'limit', label: t('observability.labels.limit'), color: 'info', count: sb.limit },
      { key: 'other', label: t('observability.labels.other'), color: 'secondary', count: sb.other },
    ].filter((b) => b.count > 0)
  }, [metrics, t])

  const hasMetrics = metrics && metrics.statusBreakdown.total > 0

  return (
    <CCard>
      <CCardHeader className="d-flex justify-content-between align-items-start flex-wrap gap-2">
        <div>
          <h4 className="mb-1">{t('observability.title')}</h4>
          <small className="text-medium-emphasis">
            {selectedStrategy
              ? t('observability.subtitle', {
                  name: selectedStrategy.name,
                  version: selectedStrategy.version,
                })
              : t('observability.subtitleEmpty')}
          </small>
        </div>
        <div className="d-flex gap-2">
          <CButton color="secondary" variant="outline" onClick={goCompare}>
            {t('observability.compareCta')}
          </CButton>
        </div>
      </CCardHeader>
      <CCardBody>
        <CForm className="mb-3">
          <CRow className="g-2 align-items-end">
            <CCol md={6}>
              <label className="form-label small text-medium-emphasis" htmlFor="obs-strategy">
                {t('observability.pickerLabel')}
              </label>
              <CFormSelect
                id="obs-strategy"
                value={selectedId}
                disabled={isLoadingList}
                onChange={(e) => setSelectedId(e.target.value)}
              >
                <option value="">{t('observability.pickerPlaceholder')}</option>
                {strategies.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name} · v{s.version} · {s.status}
                  </option>
                ))}
              </CFormSelect>
            </CCol>
            <CCol md={4}>
              <label className="form-label small text-medium-emphasis" htmlFor="obs-window">
                {t('observability.windowLabel')}
              </label>
              <CFormSelect
                id="obs-window"
                value={windowKey}
                onChange={(e) => setWindowKey(e.target.value)}
              >
                {WINDOW_OPTIONS.map((opt) => (
                  <option key={opt} value={opt}>
                    {t(`observability.window.${opt}`)}
                  </option>
                ))}
              </CFormSelect>
            </CCol>
            <CCol md={2}>
              <CButton
                color="secondary"
                variant="outline"
                className="w-100"
                onClick={() => loadMetrics(selectedId, windowKey)}
                disabled={!selectedId || isLoadingMetrics}
              >
                {t('observability.refresh')}
              </CButton>
            </CCol>
          </CRow>
        </CForm>

        {listError && <CAlert color="danger">{listError}</CAlert>}
        {metricsError && <CAlert color="danger">{metricsError}</CAlert>}

        {isLoadingMetrics && (
          <CRow className="g-3">
            {[0, 1, 2, 3].map((i) => (
              <CCol md={6} key={i}>
                <CCard>
                  <SkeletonCard lines={4} />
                </CCard>
              </CCol>
            ))}
          </CRow>
        )}

        {!isLoadingMetrics && selectedId && metrics && !hasMetrics && (
          <CAlert color="info">{t('observability.noData')}</CAlert>
        )}

        {!isLoadingMetrics && hasMetrics && (
          <CRow className="g-3">
            <CCol md={6}>
              <CCard className="h-100">
                <CCardHeader>{t('observability.cards.statusTitle')}</CCardHeader>
                <CCardBody>
                  <div className="d-flex flex-wrap gap-4 mb-3">
                    <StatChip
                      color="success"
                      label={t('observability.labels.successRate')}
                      value={formatPct(metrics.successRate)}
                      sub={`${metrics.statusBreakdown.ok} / ${metrics.statusBreakdown.total}`}
                    />
                    <StatChip
                      color="danger"
                      label={t('observability.labels.errorRate')}
                      value={formatPct(metrics.errorRate)}
                      sub={`${
                        metrics.statusBreakdown.error +
                        metrics.statusBreakdown.timeout +
                        metrics.statusBreakdown.limit
                      } / ${metrics.statusBreakdown.total}`}
                    />
                    <StatChip
                      color="dark"
                      label={t('observability.labels.total')}
                      value={metrics.statusBreakdown.total}
                    />
                  </div>
                  {statusBars.length > 0 && (
                    <CProgressStacked className="mb-2">
                      {statusBars.map((b) => (
                        <CProgress
                          key={b.key}
                          color={b.color}
                          value={(b.count / metrics.statusBreakdown.total) * 100}
                          aria-label={`${b.label}: ${b.count}`}
                        />
                      ))}
                    </CProgressStacked>
                  )}
                  <div className="d-flex flex-wrap gap-3 mt-2">
                    {statusBars.map((b) => (
                      <small key={b.key}>
                        <CBadge color={b.color} className="me-1">
                          {b.label}
                        </CBadge>
                        {b.count}
                      </small>
                    ))}
                  </div>
                </CCardBody>
              </CCard>
            </CCol>

            <CCol md={6}>
              <CCard className="h-100">
                <CCardHeader>{t('observability.cards.latencyTitle')}</CCardHeader>
                <CCardBody>
                  <CRow className="g-2 mb-3">
                    <CCol xs={6} md={4}>
                      <small className="text-medium-emphasis d-block">
                        {t('observability.labels.avg')}
                      </small>
                      <span className="fw-semibold">{formatMs(metrics.duration.avgMs)}</span>
                    </CCol>
                    <CCol xs={6} md={4}>
                      <small className="text-medium-emphasis d-block">
                        {t('observability.labels.p50')}
                      </small>
                      <span className="fw-semibold">{formatMs(metrics.duration.p50Ms)}</span>
                    </CCol>
                    <CCol xs={6} md={4}>
                      <small className="text-medium-emphasis d-block">
                        {t('observability.labels.p95')}
                      </small>
                      <span className="fw-semibold">{formatMs(metrics.duration.p95Ms)}</span>
                    </CCol>
                    <CCol xs={6} md={4}>
                      <small className="text-medium-emphasis d-block">
                        {t('observability.labels.p99')}
                      </small>
                      <span className="fw-semibold">{formatMs(metrics.duration.p99Ms)}</span>
                    </CCol>
                    <CCol xs={6} md={4}>
                      <small className="text-medium-emphasis d-block">
                        {t('observability.labels.max')}
                      </small>
                      <span className="fw-semibold">{formatMs(metrics.duration.maxMs)}</span>
                    </CCol>
                    <CCol xs={6} md={4}>
                      <small className="text-medium-emphasis d-block">
                        {t('observability.labels.samples')}
                      </small>
                      <span className="fw-semibold">{metrics.duration.sampleSize}</span>
                    </CCol>
                  </CRow>
                  <HistogramBars
                    buckets={metrics.durationHistogram}
                    emptyLabel={t('observability.labels.samples')}
                  />
                </CCardBody>
              </CCard>
            </CCol>

            <CCol md={6}>
              <CCard className="h-100">
                <CCardHeader>{t('observability.cards.errorsTitle')}</CCardHeader>
                <CCardBody>
                  {metrics.topErrors.length === 0 ? (
                    <p className="text-medium-emphasis mb-0">
                      {t('observability.labels.noErrors')}
                    </p>
                  ) : (
                    <CTable small responsive className="mb-0">
                      <CTableHead>
                        <CTableRow>
                          <CTableHeaderCell>{t('observability.labels.code')}</CTableHeaderCell>
                          <CTableHeaderCell className="text-end">
                            {t('observability.labels.count')}
                          </CTableHeaderCell>
                        </CTableRow>
                      </CTableHead>
                      <CTableBody>
                        {metrics.topErrors.map((e) => (
                          <CTableRow key={e.code}>
                            <CTableDataCell>
                              <code>{e.code}</code>
                            </CTableDataCell>
                            <CTableDataCell className="text-end fw-semibold">
                              {e.count}
                            </CTableDataCell>
                          </CTableRow>
                        ))}
                      </CTableBody>
                    </CTable>
                  )}
                </CCardBody>
              </CCard>
            </CCol>

            <CCol md={6}>
              <CCard className="h-100">
                <CCardHeader>{t('observability.cards.casesTitle')}</CCardHeader>
                <CCardBody>
                  {metrics.topCases.length === 0 ? (
                    <p className="text-medium-emphasis mb-0">
                      {t('observability.labels.noCases')}
                    </p>
                  ) : (
                    <CTable small responsive className="mb-0">
                      <CTableHead>
                        <CTableRow>
                          <CTableHeaderCell>{t('observability.labels.case')}</CTableHeaderCell>
                          <CTableHeaderCell className="text-end">
                            {t('observability.labels.count')}
                          </CTableHeaderCell>
                        </CTableRow>
                      </CTableHead>
                      <CTableBody>
                        {metrics.topCases.map((c, i) => (
                          <CTableRow key={`${c.caseName || 'default'}-${i}`}>
                            <CTableDataCell>
                              {c.caseName ? (
                                <code>{c.caseName}</code>
                              ) : (
                                <em className="text-medium-emphasis">
                                  {t('observability.labels.defaultCase')}
                                </em>
                              )}
                            </CTableDataCell>
                            <CTableDataCell className="text-end fw-semibold">
                              {c.count}
                            </CTableDataCell>
                          </CTableRow>
                        ))}
                      </CTableBody>
                    </CTable>
                  )}
                </CCardBody>
              </CCard>
            </CCol>

            <CCol md={6}>
              <CCard className="h-100">
                <CCardHeader>{t('observability.cards.pointsTitle')}</CCardHeader>
                <CCardBody>
                  <small className="text-medium-emphasis d-block mb-2">
                    {t('observability.labels.pointsSum')}:{' '}
                    <span className="fw-semibold">{formatNum(metrics.pointsSum, 1)}</span>
                  </small>
                  <HistogramBars
                    buckets={metrics.pointsHistogram}
                    emptyLabel={t('observability.labels.noPoints')}
                  />
                </CCardBody>
              </CCard>
            </CCol>

            <CCol md={6}>
              <CCard className="h-100">
                <CCardHeader>{t('observability.cards.nodesTitle')}</CCardHeader>
                <CCardBody>
                  <CRow className="g-2">
                    <CCol xs={6}>
                      <small className="text-medium-emphasis d-block">
                        {t('observability.labels.nodesAvg')}
                      </small>
                      <span className="fs-5 fw-semibold">{formatNum(metrics.nodesAvg, 1)}</span>
                    </CCol>
                    <CCol xs={6}>
                      <small className="text-medium-emphasis d-block">
                        {t('observability.labels.nodesMax')}
                      </small>
                      <span className="fs-5 fw-semibold">{metrics.nodesMax}</span>
                    </CCol>
                  </CRow>
                </CCardBody>
              </CCard>
            </CCol>
          </CRow>
        )}
      </CCardBody>
    </CCard>
  )
}

export default StrategyObservabilityView
