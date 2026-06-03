import React, { useEffect, useState } from 'react'
import PropTypes from 'prop-types'
import { useTranslation } from 'react-i18next'
import { CRow, CCol, CAlert, CSpinner } from '@coreui/react'
import { API_URL, fetcher } from '@utils/api'
import WidgetKpi from './WidgetKpi'

const EMPTY_SUMMARY = {
  new_users: [],
  games_opened: [],
  points_earned: [],
  actions_performed: [],
}

const WidgetsDropdown = (props) => {
  const { t } = useTranslation('dashboard')
  const [data, setData] = useState(EMPTY_SUMMARY)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    const fetchData = async () => {
      setLoading(true)
      setError(null)
      try {
        const responseRequest = await fetcher(`${API_URL}dashboard/summary?group_by=month`, {
          method: 'GET',
        })
        const response = await responseRequest.json()
        if (!cancelled) setData({ ...EMPTY_SUMMARY, ...response })
      } catch (err) {
        console.error('Error fetching dashboard summary:', err)
        if (!cancelled) setError(err)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    fetchData()
    return () => {
      cancelled = true
    }
  }, [])

  if (error) {
    return (
      <CAlert color="danger" className={props.className}>
        {t('widgets.loadError')}
      </CAlert>
    )
  }

  if (loading) {
    return (
      <div className={`d-flex justify-content-center py-5 ${props.className || ''}`}>
        <CSpinner color="primary" />
      </div>
    )
  }

  return (
    <CRow className={props.className} xs={{ gutter: 4 }}>
      <CCol sm={6} xl={4} xxl={3}>
        <WidgetKpi
          dataWidget={data.new_users}
          title={t('widgets.newUsers')}
          color="primary"
        />
      </CCol>
      <CCol sm={6} xl={4} xxl={3}>
        <WidgetKpi
          dataWidget={data.games_opened}
          title={t('widgets.gamesOpened')}
          color="info"
        />
      </CCol>
      <CCol sm={6} xl={4} xxl={3}>
        <WidgetKpi
          dataWidget={data.points_earned}
          title={t('widgets.pointsRewarded')}
          color="warning"
          fill
        />
      </CCol>
      <CCol sm={6} xl={4} xxl={3}>
        <WidgetKpi
          dataWidget={data.actions_performed}
          title={t('widgets.actionsPerformed')}
          tooltip={t('widgets.actionsTooltip')}
          color="danger"
          variant="bar"
        />
      </CCol>
    </CRow>
  )
}

WidgetsDropdown.propTypes = {
  className: PropTypes.string,
}

export default WidgetsDropdown
