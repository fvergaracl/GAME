// Sprint 5: a points-per-iteration chart for cumulative simulation runs.
// The table already lists every run; the chart makes the *shape* of the
// curve obvious — does the strategy plateau, accelerate, or cap out as the
// accumulated values grow? Two series: points granted per run (bars) and
// the running total (line).

import React, { useMemo } from 'react'
import PropTypes from 'prop-types'
import { useTranslation } from 'react-i18next'
import { CChart } from '@coreui/react-chartjs'

export default function SimulationRunsChart({ runs }) {
  const { t } = useTranslation('editor')

  const data = useMemo(() => {
    const labels = runs.map((r) => String(r.run))
    const perRun = runs.map((r) => Number(r.points) || 0)
    let acc = 0
    const cumulative = perRun.map((p) => {
      acc += p
      return acc
    })
    return { labels, perRun, cumulative }
  }, [runs])

  if (!runs || runs.length === 0) return null

  return (
    <div className="mt-3">
      <h6>{t('simulate.chartTitle')}</h6>
      <CChart
        type="bar"
        height={180}
        data={{
          labels: data.labels,
          datasets: [
            {
              type: 'line',
              label: t('simulate.chartCumulative'),
              data: data.cumulative,
              borderColor: 'rgba(45, 154, 87, 0.9)',
              backgroundColor: 'rgba(45, 154, 87, 0.2)',
              borderWidth: 2,
              tension: 0.3,
              yAxisID: 'y',
              order: 0,
            },
            {
              type: 'bar',
              label: t('simulate.chartPerRun'),
              data: data.perRun,
              backgroundColor: 'rgba(51, 153, 255, 0.5)',
              borderColor: 'rgba(51, 153, 255, 0.9)',
              borderWidth: 1,
              yAxisID: 'y',
              order: 1,
            },
          ],
        }}
        options={{
          maintainAspectRatio: false,
          plugins: {
            legend: { display: true, position: 'bottom', labels: { boxWidth: 12 } },
          },
          scales: {
            x: { title: { display: true, text: t('simulate.chartXAxis') } },
            y: { beginAtZero: true, title: { display: true, text: t('simulate.pointsColumn') } },
          },
        }}
      />
    </div>
  )
}

SimulationRunsChart.propTypes = {
  runs: PropTypes.arrayOf(
    PropTypes.shape({
      run: PropTypes.number,
      points: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
      caseName: PropTypes.string,
    }),
  ),
}
