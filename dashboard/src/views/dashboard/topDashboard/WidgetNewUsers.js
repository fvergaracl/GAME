import React, { useEffect, useRef } from 'react'
import PropTypes from 'prop-types'

import { CWidgetStatsA } from '@coreui/react'
import { getStyle } from '@coreui/utils'
import { CChartLine } from '@coreui/react-chartjs'
import CIcon from '@coreui/icons-react'
import { cilArrowBottom, cilArrowTop } from '@coreui/icons'

const WidgetNewUsers = ({ dataWidget }) => {
  const widgetChartRef = useRef(null)

  useEffect(() => {
    document.documentElement.addEventListener('ColorSchemeChange', () => {
      if (widgetChartRef.current) {
        setTimeout(() => {
          widgetChartRef.current.data.datasets[0].pointBackgroundColor = getStyle('--cui-primary')
          widgetChartRef.current.update()
        })
      }
    })
  }, [widgetChartRef])

  dataWidget.sort((a, b) => parseInt(a.label, 10) - parseInt(b.label, 10))
  // convert label to month name
  const monthNames = [
    'January',
    'February',
    'March',
    'April',
    'May',
    'June',
    'July',
    'August',
    'September',
    'October',
    'November',
    'December',
  ]

  const data = {
    labels: dataWidget.map((item) => monthNames[parseInt(item.label, 10) - 1]),
    datasets: [
      {
        label: 'New Users',
        backgroundColor: 'transparent',
        borderColor: 'rgba(255,255,255,.55)',
        pointBackgroundColor: getStyle('--cui-primary'),
        data: dataWidget.map((item) => parseInt(item?.count || 0, 10)),
      },
    ],
  }

  const numberNewUsersLastMonth = dataWidget.reverse()?.[0]?.count
  const diffNewUsersPercentage =
    ((dataWidget?.[0]?.count - dataWidget?.[1]?.count) / dataWidget?.[1]?.count) * 100 || 0
  const IconArrow = () =>
    diffNewUsersPercentage === 0 ? (
      <></>
    ) : diffNewUsersPercentage > 0 ? (
      <CIcon icon={cilArrowTop} />
    ) : (
      <CIcon icon={cilArrowBottom} />
    )

  const minValue = Math.min(...data.datasets[0].data) - 5
  const maxValue = Math.max(...data.datasets[0].data) + 5

  return (
    <CWidgetStatsA
      color="primary"
      value={
        <>
          {numberNewUsersLastMonth}{' '}
          <span className="fs-6 fw-normal">
            ({diffNewUsersPercentage}% )
            <IconArrow />
          </span>
        </>
      }
      title="New users"
      chart={
        <CChartLine
          ref={widgetChartRef}
          className="mt-3 mx-3"
          style={{ height: '70px' }}
          data={data}
          options={{
            plugins: {
              legend: {
                display: false,
              },
            },
            maintainAspectRatio: false,
            scales: {
              x: {
                border: {
                  display: false,
                },
                grid: {
                  display: false,
                  drawBorder: false,
                },
                ticks: {
                  display: false,
                },
              },
              y: {
                min: minValue,
                max: maxValue,
                display: false,
                grid: {
                  display: false,
                },
                ticks: {
                  display: false,
                },
              },
            },
            elements: {
              line: {
                borderWidth: 1,
                tension: 0.4,
              },
              point: {
                radius: 4,
                hitRadius: 10,
                hoverRadius: 4,
              },
            },
          }}
        />
      }
    />
  )
}

WidgetNewUsers.propTypes = {
  dataWidget: PropTypes.array || PropTypes.arrayOf(PropTypes.object),
}

export default WidgetNewUsers
