import React, { useState } from 'react'
import PropTypes from 'prop-types'
import DatePicker from 'react-datepicker'
import { CButton } from '@coreui/react'
import 'react-datepicker/dist/react-datepicker.css'

const DateRangePicker = ({ customRange, setCustomRange, onFilter }) => {
  const handleDateChange = (dates) => {
    const [start, end] = dates
    setCustomRange((prev) => ({
      ...prev,
      start,
      end,
    }))
  }

  return (
    <div
      style={{
        position: 'relative',
        display: 'inline-block',
        textAlign: 'center',
        // paddingBottom: '50px',
      }}
    >
      <DatePicker
        selected={customRange.start}
        onChange={handleDateChange}
        startDate={customRange.start}
        endDate={customRange.end}
        selectsRange
        highlightDates={[new Date()]}
        inline
      />
      {/* {customRange.start && customRange.end && (
        <CButton
          color="primary"
          onClick={onFilter}
          style={{
            position: 'absolute',
            bottom: '10px',
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 10,
            width: '200px',
          }}
        >
          Filter
        </CButton>
      )} */}
    </div>
  )
}

DateRangePicker.propTypes = {
  customRange: PropTypes.shape({
    start: PropTypes.instanceOf(Date),
    end: PropTypes.instanceOf(Date),
  }),
  setCustomRange: PropTypes.func,
  onFilter: PropTypes.func,
}

DateRangePicker.defaultProps = {
  customRange: {
    start: new Date(new Date().setFullYear(new Date().getFullYear() - 1)),
    end: new Date(),
  },
  setCustomRange: () => {},
  onFilter: () => {},
}

export default DateRangePicker
