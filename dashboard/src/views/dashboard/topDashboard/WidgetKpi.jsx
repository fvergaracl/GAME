import React, { useEffect, useMemo, useRef } from 'react'
import PropTypes from 'prop-types'

import { CWidgetStatsA, CTooltip } from '@coreui/react'
import { getStyle } from '@coreui/utils'
import { CChartBar, CChartLine } from '@coreui/react-chartjs'
import CIcon from '@coreui/icons-react'
import { cilArrowBottom, cilArrowTop, cilInfo } from '@coreui/icons'

// Sprint 11: single reusable KPI widget for the dashboard header row.
//
// Replaces four near-identical copies (WidgetNewUsers / WidgetGamesOpened /
// WidgetPointsRewarded / WidgetActionsPerformanced) that each carried the
// same bugs:
//   - ``Math.min(...[])``/``Math.max(...[])`` on an empty series yields
//     ±Infinity, which collapses the chart's y-axis and renders a blank
//     sparkline whenever the backend returns no rows.
//   - the latest value rendered as ``undefined`` (blank) instead of 0.
//   - the trend % was an unrounded float and was derived by mutating the
//     ``dataWidget`` prop in place via ``.sort()``/``.reverse()``.
//
// The series is sorted by numeric label (the backend buckets by month →
// "01".."12") into a local copy, so props are never mutated.

const MONTH_NAMES = [
  'Jan',
  'Feb',
  'Mar',
  'Apr',
  'May',
  'Jun',
  'Jul',
  'Aug',
  'Sep',
  'Oct',
  'Nov',
  'Dec',
]

// CoreUI widget ``color`` → the CSS custom property used to tint chart points.
const POINT_COLOR_VAR = {
  primary: '--cui-primary',
  info: '--cui-info',
  warning: '--cui-warning',
  danger: '--cui-danger',
  success: '--cui-success',
}

const labelToName = (label) => {
  const month = parseInt(label, 10)
  return month >= 1 && month <= 12 ? MONTH_NAMES[month - 1] : String(label ?? '')
}

const WidgetKpi = ({ dataWidget = [], title, tooltip, color = 'primary', variant = 'line', fill = false }) => {
  const chartRef = useRef(null)
  const pointColorVar = POINT_COLOR_VAR[color] || POINT_COLOR_VAR.primary

  // Keep chart point colors in sync with light/dark theme switches.
  useEffect(() => {
    const handler = () => {
      const chart = chartRef.current
      if (!chart) return
      setTimeout(() => {
        chart.data.datasets[0].pointBackgroundColor = getStyle(pointColorVar)
        chart.update()
      })
    }
    document.documentElement.addEventListener('ColorSchemeChange', handler)
    return () => document.documentElement.removeEventListener('ColorSchemeChange', handler)
  }, [pointColorVar])

  // Derive everything from a sorted *copy* so the prop array is never mutated.
  const { labels, counts, latest, diffPct } = useMemo(() => {
    const sorted = [...dataWidget].sort(
      (a, b) => parseInt(a.label, 10) - parseInt(b.label, 10),
    )
    const series = sorted.map((item) => Number(item?.count) || 0)
    const last = series.length ? series[series.length - 1] : 0
    const prev = series.length > 1 ? series[series.length - 2] : 0
    const pct = prev ? ((last - prev) / prev) * 100 : 0
    return {
      labels: sorted.map((item) => labelToName(item.label)),
      counts: series,
      latest: last,
      diffPct: pct,
    }
  }, [dataWidget])

  const hasData = counts.length > 0
  const minValue = hasData ? Math.min(...counts) - 5 : 0
  const maxValue = hasData ? Math.max(...counts) + 5 : 10

  const trendLabel =
    diffPct === 0 ? '0%' : `${diffPct > 0 ? '+' : ''}${diffPct.toFixed(1)}%`
  const TrendIcon = () =>
    diffPct === 0 ? null : (
      <CIcon icon={diffPct > 0 ? cilArrowTop : cilArrowBottom} className="ms-1" />
    )

  const chartData = {
    labels,
    datasets: [
      {
        label: title,
        backgroundColor: fill ? 'rgba(255,255,255,.2)' : 'transparent',
        borderColor: 'rgba(255,255,255,.55)',
        pointBackgroundColor: getStyle(pointColorVar),
        fill,
        data: counts,
        ...(variant === 'bar' ? { barPercentage: 0.6 } : {}),
      },
    ],
  }

  const lineOptions = {
    plugins: { legend: { display: false } },
    maintainAspectRatio: false,
    scales: {
      x: {
        border: { display: false },
        grid: { display: false, drawBorder: false },
        ticks: { display: false },
      },
      y: {
        min: minValue,
        max: maxValue,
        display: false,
        grid: { display: false },
        ticks: { display: false },
      },
    },
    elements: {
      line: { borderWidth: fill ? 2 : 1, tension: 0.4 },
      point: { radius: fill ? 0 : 4, hitRadius: 10, hoverRadius: 4 },
    },
  }

  const barOptions = {
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: {
        grid: { display: false, drawTicks: false },
        ticks: { display: false },
      },
      y: {
        border: { display: false },
        grid: { display: false, drawBorder: false, drawTicks: false },
        ticks: { display: false },
      },
    },
  }

  const chart =
    variant === 'bar' ? (
      <CChartBar
        ref={chartRef}
        className="mt-3 mx-3"
        style={{ height: '70px' }}
        data={chartData}
        options={barOptions}
      />
    ) : (
      <CChartLine
        ref={chartRef}
        className="mt-3 mx-3"
        style={{ height: '70px' }}
        data={chartData}
        options={lineOptions}
      />
    )

  return (
    <CWidgetStatsA
      color={color}
      value={
        <>
          {latest.toLocaleString()}{' '}
          <span className="fs-6 fw-normal">
            ({trendLabel}
            <TrendIcon />)
          </span>
        </>
      }
      title={
        tooltip ? (
          <>
            {title}{' '}
            <CTooltip content={tooltip}>
              <CIcon icon={cilInfo} className="ms-1" style={{ cursor: 'pointer' }} />
            </CTooltip>
          </>
        ) : (
          title
        )
      }
      chart={chart}
    />
  )
}

WidgetKpi.propTypes = {
  dataWidget: PropTypes.arrayOf(PropTypes.object),
  title: PropTypes.string.isRequired,
  tooltip: PropTypes.string,
  color: PropTypes.oneOf(['primary', 'info', 'warning', 'danger', 'success']),
  variant: PropTypes.oneOf(['line', 'bar']),
  fill: PropTypes.bool,
}

export default WidgetKpi
