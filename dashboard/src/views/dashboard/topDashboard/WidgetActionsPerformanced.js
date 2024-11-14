import React, { useEffect, useRef } from 'react'
import PropTypes from 'prop-types'

import { CWidgetStatsA, CTooltip } from '@coreui/react'
import { getStyle } from '@coreui/utils'
import { CChartBar } from '@coreui/react-chartjs'
import CIcon from '@coreui/icons-react'
import { cilArrowBottom, cilArrowTop, cilInfo } from '@coreui/icons'

const WidgetActionsPerformanced = ({ dataWidget }) => {
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
        label: 'Actions Performance',
        backgroundColor: 'rgba(255,255,255,.2)',
        borderColor: 'rgba(255,255,255,.55)',
        data: dataWidget.map((item) => parseInt(item?.count || 0, 10)),
        barPercentage: 0.6,
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

  return (
    <CWidgetStatsA
      color="danger"
      value={
        <>
          {numberNewUsersLastMonth}{' '}
          <span className="fs-6 fw-normal">
            ({diffNewUsersPercentage}% )
            <IconArrow />
          </span>
        </>
      }
      title={
        <>
          Actions Performed{' '}
          <CTooltip content="This is the total number of actions performed by users in tasks">
            <CIcon icon={cilInfo} className="ms-1" style={{ cursor: 'pointer' }} />
          </CTooltip>
        </>
      }
      chart={
        <CChartBar
          ref={widgetChartRef}
          className="mt-3 mx-3"
          style={{ height: '70px' }}
          data={data}
          options={{
            maintainAspectRatio: false,
            plugins: {
              legend: {
                display: false,
              },
            },
            scales: {
              x: {
                grid: {
                  display: false,
                  drawTicks: false,
                },
                ticks: {
                  display: false,
                },
              },
              y: {
                border: {
                  display: false,
                },
                grid: {
                  display: false,
                  drawBorder: false,
                  drawTicks: false,
                },
                ticks: {
                  display: false,
                },
              },
            },
          }}
        />
      }
    />
  )
}

WidgetActionsPerformanced.propTypes = {
  dataWidget: PropTypes.array || PropTypes.arrayOf(PropTypes.object),
}

export default WidgetActionsPerformanced
