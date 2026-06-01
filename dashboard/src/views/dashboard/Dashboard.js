import React, { useState } from 'react'
import { CCardBody, CCol, CRow, CButton, CButtonGroup } from '@coreui/react'
import WidgetsDropdown from './topDashboard/WidgetsDropdown'
import ApiActivityChart from './bodyDashboard/ApiActivityChart'
import DateRangePicker from '../../components/DateRangePicker'

const Dashboard = () => {
  const [range, setRange] = useState('30') // Default range: 30 days
  const [customRange, setCustomRange] = useState({
    start: new Date(),
    end: new Date(),
  })

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
    <>
      <WidgetsDropdown className="mb-4" />
      <CCardBody>
        <CRow>
          <CCol sm={12}>
            <div className="gd-range-toolbar position-relative float-end mb-3">
              <CButtonGroup>
                <CButton
                  color="primary"
                  onClick={() => handleRangeChange('30')}
                  active={range === '30'}
                >
                  30 Days
                </CButton>
                <CButton
                  color="primary"
                  onClick={() => handleRangeChange('90')}
                  active={range === '90'}
                >
                  90 Days
                </CButton>
                <CButton
                  color="primary"
                  onClick={() => handleRangeChange('custom')}
                  active={range === 'custom'}
                >
                  Custom Range
                </CButton>
              </CButtonGroup>
              {range === 'custom' && (
                <div className="gd-date-popover position-absolute end-0 bg-body shadow rounded p-2">
                  <DateRangePicker customRange={customRange} setCustomRange={setCustomRange} />
                </div>
              )}
            </div>
          </CCol>
          <CCol sm={12}>
            {customRange?.end && customRange?.start && (
              <ApiActivityChart customRange={customRange} range={range} />
            )}
          </CCol>
        </CRow>
      </CCardBody>
    </>
  )
}

export default Dashboard
