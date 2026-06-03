// Sprint 10: compact language switcher used in the strategy editor
// toolbar. Sits next to the Save/Test buttons rather than in the
// global header so the change is self-contained — global app
// internationalisation is intentionally out of scope for this sprint.
//
// The component is reactive: changing the dropdown calls
// ``i18n.changeLanguage(lng)``, which fires ``languageChanged`` and
// triggers the editor to re-apply Blockly's locale messages (handled
// inside StrategyEditor's useEffect).

import React from 'react'
import PropTypes from 'prop-types'
import { useTranslation } from 'react-i18next'
import { CFormSelect } from '@coreui/react'

import { SUPPORTED_LANGUAGES, LOCALSTORAGE_LANG_KEY } from '../i18n'

const LANGUAGE_LABELS = {
  es: 'Español',
  en: 'English',
}

const LanguageSwitcher = ({ size = 'sm' }) => {
  const { i18n, t } = useTranslation('editor')

  const onChange = (event) => {
    const next = event.target.value
    i18n.changeLanguage(next)
    // i18next-browser-languagedetector caches via localStorage, but only
    // after the next page load. Set it explicitly so the choice
    // survives an immediate refresh.
    window.localStorage.setItem(LOCALSTORAGE_LANG_KEY, next)
  }

  return (
    <CFormSelect
      size={size}
      value={i18n.resolvedLanguage || 'es'}
      onChange={onChange}
      aria-label={t('buttons.languageLabel')}
      className="w-auto d-inline-block"
    >
      {SUPPORTED_LANGUAGES.map((lng) => (
        <option key={lng} value={lng}>
          {LANGUAGE_LABELS[lng] || lng}
        </option>
      ))}
    </CFormSelect>
  )
}

LanguageSwitcher.propTypes = {
  size: PropTypes.oneOf(['sm', 'lg']),
}

export default LanguageSwitcher
