// A/B comparison view.
//
// Two strategies, same time window, rendered side by side with deltas
// computed server-side (B - A). The intended use is the README's
// "static vs adaptive" / "baseline vs experimental" workflow: an
// admin promotes a draft and wants to see whether the new version is
// actually delivering more OK runs / lower latency / different points
// distribution than the one it replaced.

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

import { compareStrategies, listCustomStrategies } from '../../api'
import { extractError } from '../../utils/errors'
import { SkeletonCard } from '../../components/Skeleton'

const WINDOW_OPTIONS = ['all', '24h', '7d', '30d']

const windowToSinceIso = (key) => {
  if (!key || key === 'all') return undefined
  const ms =
    key === '24h' ? 24 * 3600 * 1000 : key === '7d' ? 7 * 86400 * 1000 : 30 * 86400 * 1000
  return new Date(Date.now() - ms).toISOString()
}

const formatPct = (value) => `${(value * 100).toFixed(1)}%`
const formatMs = (value) => `${value.toFixed(1)} ms`
const formatNumber = (value, digits = 1) =>
  Number.isFinite(value) ? value.toFixed(digits) : '-'

// One row of the deltas table. ``better`` says whether a positive
// delta is good (success rate) or bad (latency, error rate). We render
// a coloured badge so the table reads at a glance even before the
// viewer parses the numbers.
function DeltaRow({ label, valueA, valueB, delta, betterDirection, format }) {
  // ``betterDirection`` is +1 if higher is better (success rate), -1
  // if lower is better (latency, error rate).
  const sign = Math.sign(delta) * betterDirection
  const color = sign > 0 ? 'success' : sign < 0 ? 'danger' : 'secondary'
  const { t } = useTranslation('strategies')
  const flavor = sign > 0 ? t('compare.betterLabel') : sign < 0 ? t('compare.worseLabel') : '-'
  const formatted = format(delta)
  const prefix = delta > 0 ? '+' : ''
  return (
    <CTableRow>
      <CTableDataCell className="fw-semibold">{label}</CTableDataCell>
      <CTableDataCell className="text-end">{format(valueA)}</CTableDataCell>
      <CTableDataCell className="text-end">{format(valueB)}</CTableDataCell>
      <CTableDataCell className="text-end">
        <CBadge color={color} className="me-1">
          {flavor}
        </CBadge>
        {prefix}
        {formatted}
      </CTableDataCell>
    </CTableRow>
  )
}

// Stacked status bar (proportions ok / error / timeout / limit) - same
// helper as in the observability view, kept inline because it's tiny
// and varies (no "other" bucket on the comparison summary).
function StatusBar({ breakdown }) {
  const { t } = useTranslation('strategies')
  if (!breakdown || breakdown.total === 0) return null
  const bars = [
    { key: 'ok', label: t('observability.labels.ok'), color: 'success', count: breakdown.ok },
    {
      key: 'error',
      label: t('observability.labels.error'),
      color: 'danger',
      count: breakdown.error,
    },
    {
      key: 'timeout',
      label: t('observability.labels.timeout'),
      color: 'warning',
      count: breakdown.timeout,
    },
    {
      key: 'limit',
      label: t('observability.labels.limit'),
      color: 'info',
      count: breakdown.limit,
    },
    {
      key: 'other',
      label: t('observability.labels.other'),
      color: 'secondary',
      count: breakdown.other,
    },
  ].filter((b) => b.count > 0)
  return (
    <CProgressStacked>
      {bars.map((b) => (
        <CProgress
          key={b.key}
          color={b.color}
          value={(b.count / breakdown.total) * 100}
          aria-label={`${b.label}: ${b.count}`}
        />
      ))}
    </CProgressStacked>
  )
}

const StrategyComparisonView = () => {
  const { t } = useTranslation('strategies')
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  const initialA = searchParams.get('a') || ''
  const initialB = searchParams.get('b') || ''
  const initialWindow = searchParams.get('window') || 'all'

  const [strategies, setStrategies] = useState([])
  const [idA, setIdA] = useState(initialA)
  const [idB, setIdB] = useState(initialB)
  const [windowKey, setWindowKey] = useState(initialWindow)
  const [data, setData] = useState(null)
  const [isLoadingList, setIsLoadingList] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [listError, setListError] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    const next = new URLSearchParams()
    if (idA) next.set('a', idA)
    if (idB) next.set('b', idB)
    if (windowKey && windowKey !== 'all') next.set('window', windowKey)
    setSearchParams(next, { replace: true })
  }, [idA, idB, windowKey, setSearchParams])

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

  const runComparison = useCallback(() => {
    if (!idA || !idB) {
      setError(t('compare.missingInputs'))
      setData(null)
      return undefined
    }
    if (idA === idB) {
      setError(t('compare.sameStrategy'))
      setData(null)
      return undefined
    }
    let cancelled = false
    setIsLoading(true)
    setError(null)
    compareStrategies(idA, idB, { since: windowToSinceIso(windowKey) })
      .then((payload) => {
        if (cancelled) return
        setData(payload)
      })
      .catch((err) => {
        if (cancelled) return
        setError(extractError(err, t('compare.errors.load')))
        setData(null)
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [idA, idB, windowKey, t])

  // Auto-run when both ids are set on initial mount (deep-linked from
  // the observability view). Subsequent changes wait for the explicit
  // "Compare" button so the user controls when the request fires.
  useEffect(() => {
    if (initialA && initialB && initialA !== initialB) {
      runComparison()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const swap = () => {
    setIdA(idB)
    setIdB(idA)
  }

  const avgPoints = useCallback((snapshot) => {
    if (!snapshot || !snapshot.statusBreakdown || snapshot.statusBreakdown.total === 0) return 0
    return snapshot.pointsSum / snapshot.statusBreakdown.total
  }, [])

  return (
    <CCard>
      <CCardHeader className="d-flex justify-content-between align-items-start flex-wrap gap-2">
        <div>
          <h4 className="mb-1">{t('compare.title')}</h4>
          <small className="text-medium-emphasis">{t('compare.subtitle')}</small>
        </div>
        <CButton color="link" onClick={() => navigate('/strategies/observability')}>
          {t('observability.title')}
        </CButton>
      </CCardHeader>
      <CCardBody>
        <CForm className="mb-3">
          <CRow className="g-2 align-items-end">
            <CCol md={4}>
              <label className="form-label small text-medium-emphasis" htmlFor="cmp-a">
                {t('compare.pickA')}
              </label>
              <CFormSelect
                id="cmp-a"
                value={idA}
                onChange={(e) => setIdA(e.target.value)}
                disabled={isLoadingList}
              >
                <option value="">{t('compare.pickerPlaceholder')}</option>
                {strategies.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name} · v{s.version} · {s.status}
                  </option>
                ))}
              </CFormSelect>
            </CCol>
            <CCol md={4}>
              <label className="form-label small text-medium-emphasis" htmlFor="cmp-b">
                {t('compare.pickB')}
              </label>
              <CFormSelect
                id="cmp-b"
                value={idB}
                onChange={(e) => setIdB(e.target.value)}
                disabled={isLoadingList}
              >
                <option value="">{t('compare.pickerPlaceholder')}</option>
                {strategies.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name} · v{s.version} · {s.status}
                  </option>
                ))}
              </CFormSelect>
            </CCol>
            <CCol md={2}>
              <label className="form-label small text-medium-emphasis" htmlFor="cmp-window">
                {t('compare.windowLabel')}
              </label>
              <CFormSelect
                id="cmp-window"
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
            <CCol md={2} className="d-flex flex-column gap-1">
              <CButton color="primary" onClick={runComparison} disabled={isLoading}>
                {t('compare.run')}
              </CButton>
              <CButton color="secondary" variant="outline" size="sm" onClick={swap}>
                {t('compare.swap')}
              </CButton>
            </CCol>
          </CRow>
        </CForm>

        {listError && <CAlert color="danger">{listError}</CAlert>}
        {error && <CAlert color="danger">{error}</CAlert>}

        {isLoading && (
          <CRow className="g-3">
            {[0, 1].map((i) => (
              <CCol md={6} key={i}>
                <CCard>
                  <SkeletonCard lines={5} />
                </CCard>
              </CCol>
            ))}
          </CRow>
        )}

        {!isLoading && data && (
          <>
            <CRow className="g-3 mb-3">
              <CCol md={6}>
                <CCard className="h-100">
                  <CCardHeader>
                    A · {data.a.name} <small className="text-medium-emphasis">v{data.a.version}</small>
                  </CCardHeader>
                  <CCardBody>
                    <small className="text-medium-emphasis d-block mb-1">
                      {t('observability.labels.total')}: {data.a.statusBreakdown.total}
                    </small>
                    <StatusBar breakdown={data.a.statusBreakdown} />
                    <CRow className="g-2 mt-3">
                      <CCol xs={6}>
                        <small className="text-medium-emphasis d-block">
                          {t('observability.labels.successRate')}
                        </small>
                        <span className="fw-semibold">{formatPct(data.a.successRate)}</span>
                      </CCol>
                      <CCol xs={6}>
                        <small className="text-medium-emphasis d-block">
                          {t('observability.labels.p95')}
                        </small>
                        <span className="fw-semibold">{formatMs(data.a.duration.p95Ms)}</span>
                      </CCol>
                    </CRow>
                  </CCardBody>
                </CCard>
              </CCol>
              <CCol md={6}>
                <CCard className="h-100">
                  <CCardHeader>
                    B · {data.b.name} <small className="text-medium-emphasis">v{data.b.version}</small>
                  </CCardHeader>
                  <CCardBody>
                    <small className="text-medium-emphasis d-block mb-1">
                      {t('observability.labels.total')}: {data.b.statusBreakdown.total}
                    </small>
                    <StatusBar breakdown={data.b.statusBreakdown} />
                    <CRow className="g-2 mt-3">
                      <CCol xs={6}>
                        <small className="text-medium-emphasis d-block">
                          {t('observability.labels.successRate')}
                        </small>
                        <span className="fw-semibold">{formatPct(data.b.successRate)}</span>
                      </CCol>
                      <CCol xs={6}>
                        <small className="text-medium-emphasis d-block">
                          {t('observability.labels.p95')}
                        </small>
                        <span className="fw-semibold">{formatMs(data.b.duration.p95Ms)}</span>
                      </CCol>
                    </CRow>
                  </CCardBody>
                </CCard>
              </CCol>
            </CRow>

            <CCard>
              <CCardHeader>{t('compare.deltaLabel')}</CCardHeader>
              <CCardBody>
                <CTable small responsive align="middle" className="mb-0">
                  <CTableHead>
                    <CTableRow>
                      <CTableHeaderCell>&nbsp;</CTableHeaderCell>
                      <CTableHeaderCell className="text-end">A</CTableHeaderCell>
                      <CTableHeaderCell className="text-end">B</CTableHeaderCell>
                      <CTableHeaderCell className="text-end">
                        {t('compare.deltaLabel')}
                      </CTableHeaderCell>
                    </CTableRow>
                  </CTableHead>
                  <CTableBody>
                    <DeltaRow
                      label={t('compare.summary.successRate')}
                      valueA={data.a.successRate}
                      valueB={data.b.successRate}
                      delta={data.delta.successRate}
                      betterDirection={+1}
                      format={formatPct}
                    />
                    <DeltaRow
                      label={t('compare.summary.errorRate')}
                      valueA={data.a.errorRate}
                      valueB={data.b.errorRate}
                      delta={data.delta.errorRate}
                      betterDirection={-1}
                      format={formatPct}
                    />
                    <DeltaRow
                      label={t('compare.summary.p95')}
                      valueA={data.a.duration.p95Ms}
                      valueB={data.b.duration.p95Ms}
                      delta={data.delta.p95Ms}
                      betterDirection={-1}
                      format={formatMs}
                    />
                    <DeltaRow
                      label={t('compare.summary.avg')}
                      valueA={data.a.duration.avgMs}
                      valueB={data.b.duration.avgMs}
                      delta={data.delta.avgMs}
                      betterDirection={-1}
                      format={formatMs}
                    />
                    <DeltaRow
                      label={t('compare.summary.pointsAvg')}
                      valueA={avgPoints(data.a)}
                      valueB={avgPoints(data.b)}
                      delta={data.delta.pointsAvg}
                      betterDirection={+1}
                      format={(v) => formatNumber(v, 2)}
                    />
                  </CTableBody>
                </CTable>
              </CCardBody>
            </CCard>
          </>
        )}
      </CCardBody>
    </CCard>
  )
}

export default StrategyComparisonView
