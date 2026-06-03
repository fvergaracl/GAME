import React, { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { CChartLine } from '@coreui/react-chartjs'
import PropTypes from 'prop-types'
import { API_URL, fetcher } from '@utils/api'

const ApiActivityChart = ({
  customRange = {
    start: new Date(new Date().setFullYear(new Date().getFullYear() - 1)),
    end: new Date(),
  },
  range = '30',
}) => {
  const { t } = useTranslation('dashboard')
  const [chartData, setChartData] = useState({
    labels: [],
    datasets: [],
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchData = async (startDate, endDate) => {
    setLoading(true)
    setError(null)
    try {
      let urlToFetch = `${API_URL}dashboard/summary/logs?group_by=day`
      if (startDate && endDate) {
        urlToFetch += `&start_date=${startDate}&end_date=${endDate}`
      }
      const responseRequest = await fetcher(urlToFetch, { method: 'GET' })
      const response = await responseRequest.json()

      // Defensive: the backend may omit a series entirely when it has no
      // rows for that severity, so default each one to an empty array.
      const info = response.info || []
      const success = response.success || []
      const errorSeries = response.error || []

      const labels = info.map((item) => new Date(item.label).toLocaleDateString())

      // Setting chart data
      setChartData({
        labels,
        datasets: [
          {
            label: t('activity.info'),
            data: info.map((item) => item.count),
            borderColor: '#36A2EB',
            backgroundColor: 'rgba(54, 162, 235, 0.2)',
            fill: true,
          },
          {
            label: t('activity.success'),
            data: success.map((item) => item.count),
            borderColor: '#4CAF50',
            backgroundColor: 'rgba(76, 175, 80, 0.2)',
            fill: true,
          },
          {
            label: t('activity.error'),
            data: errorSeries.map((item) => item.count),
            borderColor: '#F44336',
            backgroundColor: 'rgba(244, 67, 54, 0.2)',
            fill: true,
          },
        ],
      })
    } catch (err) {
      console.error('Error fetching data:', err)
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const now = new Date()
    let startDate
    let endDate = now.toISOString().split('T')[0]

    if (range === '30') {
      startDate = new Date(now.setDate(now.getDate() - 30)).toISOString().split('T')[0]
    } else if (range === '90') {
      startDate = new Date(now.setDate(now.getDate() - 90)).toISOString().split('T')[0]
    } else {
      startDate = customRange.start.toISOString().split('T')[0]
      endDate = customRange.end.toISOString().split('T')[0]
    }

    fetchData(startDate, endDate)
  }, [range, customRange])

  const isEmpty = !chartData.labels.length

  return (
    <div style={{ height: '20rem' }}>
      <h2 className="text-center">{t('activity.title')}</h2>
      {loading ? (
        <p className="text-center text-body-secondary">{t('activity.loading')}</p>
      ) : error ? (
        <p className="text-center text-danger">{t('widgets.loadError')}</p>
      ) : isEmpty ? (
        <p className="text-center text-body-secondary">{t('activity.empty')}</p>
      ) : (
        <CChartLine
          style={{ height: '100%' }}
          data={chartData}
          options={{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                position: 'top',
              },
            },
          }}
        />
      )}
    </div>
  )
}

ApiActivityChart.propTypes = {
  props: PropTypes.object,
  className: PropTypes.string,
  withCharts: PropTypes.bool,
  customRange: PropTypes.shape({
    start: PropTypes.instanceOf(Date),
    end: PropTypes.instanceOf(Date),
  }),
  range: PropTypes.string,
}

export default ApiActivityChart
