// Sprint 9 — Skeleton placeholders.
//
// Replaces "spinner inside an empty card" loading states. A skeleton
// keeps the layout stable (no content shift) and signals shape so the
// user has something to look at while the fetch resolves. Driven by the
// classes defined in scss/_custom.scss so dark mode "just works" via the
// CoreUI ``--cui-tertiary-bg`` token.

import React from 'react'
import PropTypes from 'prop-types'
import {
  CTable,
  CTableBody,
  CTableDataCell,
  CTableHead,
  CTableHeaderCell,
  CTableRow,
} from '@coreui/react'

const mergeStyle = (style, extra) => (extra ? { ...style, ...extra } : style)

// Single pulsing bar. Use ``width`` to vary line length so paragraph
// skeletons don't look like a perfect rectangle (which reads as a real
// block of UI rather than placeholder text).
export const Skeleton = ({ width, height, className, style, variant = 'text', ariaLabel }) => {
  const cls = [
    'gd-skeleton',
    variant === 'text' ? 'gd-skeleton--text' : '',
    variant === 'title' ? 'gd-skeleton--title' : '',
    variant === 'block' ? 'gd-skeleton--block' : '',
    variant === 'circle' ? 'gd-skeleton--circle' : '',
    className || '',
  ]
    .filter(Boolean)
    .join(' ')
  const inline = {}
  if (width != null) inline.width = typeof width === 'number' ? `${width}px` : width
  if (height != null) inline.height = typeof height === 'number' ? `${height}px` : height
  return (
    <span
      className={cls}
      style={mergeStyle(inline, style)}
      role="status"
      aria-busy="true"
      aria-label={ariaLabel || 'Loading'}
    />
  )
}

Skeleton.propTypes = {
  width: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  height: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  className: PropTypes.string,
  style: PropTypes.object,
  variant: PropTypes.oneOf(['text', 'title', 'block', 'circle']),
  ariaLabel: PropTypes.string,
}

// Paragraph-shaped block. Use this when you don't know what the content
// will look like — it's the safe default.
export const SkeletonText = ({ lines = 3, lastWidth = '60%' }) => (
  <div role="status" aria-busy="true" aria-label="Loading">
    {Array.from({ length: lines }).map((_, i) => (
      <Skeleton
        key={i}
        variant="text"
        width={i === lines - 1 ? lastWidth : '100%'}
        ariaLabel=""
      />
    ))}
  </div>
)

SkeletonText.propTypes = {
  lines: PropTypes.number,
  lastWidth: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
}

// Table skeleton: matches the shape of a typical CTable so the swap to
// real rows doesn't cause a layout jump.
export const SkeletonTable = ({ columns = 4, rows = 5, hasActions = false }) => {
  const totalCols = columns + (hasActions ? 1 : 0)
  return (
    <CTable hover responsive align="middle" aria-busy="true">
      <CTableHead>
        <CTableRow>
          {Array.from({ length: totalCols }).map((_, i) => (
            <CTableHeaderCell key={i}>
              <Skeleton variant="text" width="60%" ariaLabel="" />
            </CTableHeaderCell>
          ))}
        </CTableRow>
      </CTableHead>
      <CTableBody>
        {Array.from({ length: rows }).map((_, rowIdx) => (
          <CTableRow key={rowIdx}>
            {Array.from({ length: totalCols }).map((_, colIdx) => (
              <CTableDataCell key={colIdx}>
                <Skeleton
                  variant="text"
                  width={colIdx === 0 ? '70%' : '50%'}
                  ariaLabel=""
                />
              </CTableDataCell>
            ))}
          </CTableRow>
        ))}
      </CTableBody>
    </CTable>
  )
}

SkeletonTable.propTypes = {
  columns: PropTypes.number,
  rows: PropTypes.number,
  hasActions: PropTypes.bool,
}

// Card-shaped block — title + a few lines.
export const SkeletonCard = ({ lines = 3 }) => (
  <div className="p-3" role="status" aria-busy="true" aria-label="Loading">
    <Skeleton variant="title" ariaLabel="" />
    <SkeletonText lines={lines} />
  </div>
)

SkeletonCard.propTypes = {
  lines: PropTypes.number,
}

export default Skeleton
