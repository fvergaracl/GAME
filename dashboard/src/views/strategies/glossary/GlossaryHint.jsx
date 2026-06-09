// Sprint 8: ``<GlossaryHint term="...">`` - small ⓘ trigger that opens
// the glossary modal at a specific term.
//
// Two modes:
//   * ``iconOnly`` (default for inline use): renders only the ⓘ button.
//     Use it right after a label, badge, or column header that names a
//     DSL concept.
//   * ``inline`` (with children): wraps children and appends the ⓘ.
//     Use it when the trigger should follow visible text.
//
// The button never bubbles its click so it can sit safely inside other
// clickable rows (table cells, dropdown items).

import React from 'react'
import PropTypes from 'prop-types'
import { useTranslation } from 'react-i18next'

import { GLOSSARY_INDEX } from './index'
import { useGlossary } from './GlossaryContext'

const GlossaryHint = ({ term, children = null, className = '', ariaLabel = '' }) => {
  const { openGlossary } = useGlossary()
  const { t } = useTranslation('glossary')
  const exists = !!GLOSSARY_INDEX[term]

  // If the term id is wrong we render the children (if any) but no
  // trigger - better than a dead button. In dev this surfaces fast
  // because the ⓘ simply doesn't appear next to the offending label.
  if (!exists) {
    if (children) return <>{children}</>
    return null
  }

  const termTitle = t(`terms.${term}.title`)
  const label =
    ariaLabel ||
    t('hint.ariaLabel', { term: termTitle, defaultValue: termTitle })

  const trigger = (
    <button
      type="button"
      className="btn btn-link btn-sm p-0 align-baseline ms-1"
      style={{ lineHeight: 1, textDecoration: 'none' }}
      onClick={(e) => {
        e.preventDefault()
        e.stopPropagation()
        openGlossary(term)
      }}
      aria-label={label}
      title={label}
    >
      <span aria-hidden="true">ⓘ</span>
    </button>
  )

  if (!children) {
    return <span className={className}>{trigger}</span>
  }

  return (
    <span className={className}>
      {children}
      {trigger}
    </span>
  )
}

GlossaryHint.propTypes = {
  term: PropTypes.string.isRequired,
  children: PropTypes.node,
  className: PropTypes.string,
  ariaLabel: PropTypes.string,
}

export default GlossaryHint
