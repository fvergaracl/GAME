import React, { useState, useEffect } from 'react'
import { CChartLine } from '@coreui/react-chartjs'
import { CButton, CButtonGroup } from '@coreui/react'
import DatePicker from 'react-datepicker'
import 'react-datepicker/dist/react-datepicker.css'
import PropTypes from 'prop-types'
import { API_URL, fetcher } from '@utils/api'

const ApiActivityChart = ({ customRange, range }) => {
  const [chartData, setChartData] = useState({
    labels: [],
    datasets: [],
  })
  const [loading, setLoading] = useState(false)

  const fetchData = async (startDate, endDate) => {
    setLoading(true)
    try {
      let urlToFetch = `${API_URL}dashboard/summary/logs?group_by=day`
      if (startDate && endDate) {
        urlToFetch += `&start_date=${startDate}&end_date=${endDate}`
      }
      const responseRequest = await fetcher(urlToFetch, { method: 'GET' })
      const response = await responseRequest.json()

      const labels = response.info.map((item) => new Date(item.label).toLocaleDateString())
      const infoData = response.info.map((item) => item.count)
      const successData = response.success.map((item) => item.count)
      const errorData = response.error.map((item) => item.count)

      // Setting chart data
      setChartData({
        labels,
        datasets: [
          {
            label: 'Info',
            data: infoData,
            borderColor: '#36A2EB',
            backgroundColor: 'rgba(54, 162, 235, 0.2)',
            fill: true,
          },
          {
            label: 'Success',
            data: successData,
            borderColor: '#4CAF50',
            backgroundColor: 'rgba(76, 175, 80, 0.2)',
            fill: true,
          },
          {
            label: 'Error',
            data: errorData,
            borderColor: '#F44336',
            backgroundColor: 'rgba(244, 67, 54, 0.2)',
            fill: true,
          },
        ],
      })
    } catch (error) {
      console.error('Error fetching data:', error)
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

  const handleRangeChange = (newRange) => {
    setRange(newRange)
    if (newRange !== 'custom') {
      const now = new Date()
      setCustomRange({
        start: new Date(now.setDate(now.getDate() - Number(newRange))),
        end: new Date(),
      })
    }
  }

  return (
    <div style={{ height: '20rem' }}>
      <h2 className="text-center">API activity logs</h2>
      {loading ? (
        <p>Loading...</p>
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

ApiActivityChart.defaultProps = {
  withCharts: true,
  customRange: {
    start: new Date(new Date().setFullYear(new Date().getFullYear() - 1)),
    end: new Date(),
  },
  range: '30',
}

export default ApiActivityChart
