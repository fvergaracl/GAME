import React, { useEffect, useRef, useState } from 'react'
import PropTypes from 'prop-types'
import { CRow, CCol } from '@coreui/react'
import { getStyle } from '@coreui/utils'
import { API_URL, fetcher } from '@utils/api'
import WidgetNewUsers from './WidgetNewUsers'
import WidgetGamesOpened from './WidgetGamesOpened'
import WidgetPointsRewarded from './WidgetPointsRewarded'
import WidgetActionsPerformanced from './WidgetActionsPerformanced'

const WidgetsDropdown = (props) => {
  const [data, setData] = useState([])
  const widgetChartRefUsers = useRef(null)
  const widgetChartRef2 = useRef(null)

  useEffect(() => {
    document.documentElement.addEventListener('ColorSchemeChange', () => {
      if (widgetChartRefUsers.current) {
        setTimeout(() => {
          widgetChartRefUsers.current.data.datasets[0].pointBackgroundColor =
            getStyle('--cui-primary')
          widgetChartRefUsers.current.update()
        })
      }

      if (widgetChartRef2.current) {
        setTimeout(() => {
          widgetChartRef2.current.data.datasets[0].pointBackgroundColor = getStyle('--cui-info')
          widgetChartRef2.current.update()
        })
      }
    })
  }, [widgetChartRefUsers, widgetChartRef2])

  useEffect(() => {
    const fetchData = async () => {
      const responseRequest = await fetcher(`${API_URL}dashboard/summary?group_by=month`, {
        method: 'GET',
      })

      const response = await responseRequest.json()
      console.log('response', response)
      setData(response)
    }

    fetchData()
  }, [])

  return (
    <CRow className={props.className} xs={{ gutter: 4 }}>
      <CCol sm={6} xl={4} xxl={3}>
        <WidgetNewUsers dataWidget={data?.new_users || []} />
      </CCol>
      <CCol sm={6} xl={4} xxl={3}>
        <WidgetGamesOpened dataWidget={data?.games_opened || []} />
      </CCol>
      <CCol sm={6} xl={4} xxl={3}>
        <WidgetPointsRewarded dataWidget={data?.points_earned || []} />
      </CCol>
      <CCol sm={6} xl={4} xxl={3}>
        <WidgetActionsPerformanced dataWidget={data?.actions_performed || []} />
      </CCol>
    </CRow>
  )
}

WidgetsDropdown.propTypes = {
  props: PropTypes.object,
  className: PropTypes.string,
  withCharts: PropTypes.bool,
}

WidgetsDropdown.defaultProps = {
  withCharts: true,
}

export default WidgetsDropdown
