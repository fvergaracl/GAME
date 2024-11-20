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
            <div style={{ position: 'relative', marginBottom: '20px', float: 'right' }}>
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
                <div
                  style={{
                    position: 'absolute',
                    top: '100%', // Justo debajo del botón
                    right: '0', // Posiciona el DateRangePicker a la derecha
                    zIndex: 9999, // Asegura que esté por encima de otros elementos
                    background: 'white',
                    boxShadow: '0px 4px 6px rgba(0, 0, 0, 0.1)',
                    borderRadius: '8px',
                    padding: '10px',
                  }}
                >
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
