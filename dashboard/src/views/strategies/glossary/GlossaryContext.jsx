// Glossary context + modal.
//
// Provides a single GlossaryModal mounted at layout level so any view
// can call ``useGlossary().openGlossary(termId)`` to pop the definition
// without each view embedding its own modal. The modal lets the user
// navigate between the index and an individual term, plus the term's
// "related" cross-links.
//
// The provider also tolerates calls before it is mounted (returns a
// no-op shim) so isolated tests that render a child without the layout
// don't have to wrap with the provider just to assert on text.

import React, {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from 'react'
import PropTypes from 'prop-types'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  CButton,
  CListGroup,
  CListGroupItem,
  CModal,
  CModalBody,
  CModalFooter,
  CModalHeader,
  CModalTitle,
} from '@coreui/react'

import { GLOSSARY_INDEX, GLOSSARY_TERMS } from './index'

const GlossaryContext = createContext(null)

const NOOP_GLOSSARY = {
  openGlossary: () => {},
  closeGlossary: () => {},
  isOpen: false,
  termId: null,
  navigateTo: () => {},
}

export const useGlossary = () => {
  const ctx = useContext(GlossaryContext)
  return ctx || NOOP_GLOSSARY
}

const GlossaryModal = () => {
  const ctx = useContext(GlossaryContext)
  const { t } = useTranslation('glossary')
  // No provider → nothing to render. This branch is for unit tests that
  // exercise GlossaryHint directly; in the running app GlossaryProvider
  // is always mounted by DefaultLayout.
  if (!ctx) return null
  const { isOpen, closeGlossary, termId, navigateTo } = ctx

  const currentTerm = termId ? GLOSSARY_INDEX[termId] : null
  const showIndex = !currentTerm

  const title = currentTerm
    ? t(`terms.${currentTerm.id}.title`)
    : t('modal.title')

  return (
    <CModal
      visible={isOpen}
      onClose={closeGlossary}
      size="lg"
      aria-labelledby="gd-glossary-title"
    >
      <CModalHeader>
        <CModalTitle id="gd-glossary-title">{title}</CModalTitle>
      </CModalHeader>
      <CModalBody>
        {showIndex ? (
          <>
            <p className="text-medium-emphasis">{t('modal.subtitle')}</p>
            <h6 className="mt-3">{t('modal.indexHeader')}</h6>
            <CListGroup>
              {GLOSSARY_TERMS.map((term) => (
                <CListGroupItem
                  key={term.id}
                  as="button"
                  type="button"
                  onClick={() => navigateTo(term.id)}
                  className="text-start"
                >
                  <strong>{t(`terms.${term.id}.title`)}</strong>
                </CListGroupItem>
              ))}
            </CListGroup>
          </>
        ) : (
          <>
            <CButton
              color="link"
              className="p-0 mb-2"
              onClick={() => navigateTo(null)}
            >
              {t('modal.backToIndex')}
            </CButton>
            <p style={{ whiteSpace: 'pre-line' }}>
              {t(`terms.${currentTerm.id}.body`)}
            </p>
            {currentTerm.blockSlug && (
              <p>
                <Link
                  to={`/strategies/blocks-help/${currentTerm.blockSlug}`}
                  onClick={closeGlossary}
                >
                  {t('modal.blockHintLabel')}
                </Link>
              </p>
            )}
            {currentTerm.related && currentTerm.related.length > 0 && (
              <>
                <h6 className="mt-3">{t('modal.relatedHeader')}</h6>
                <ul className="mb-0">
                  {currentTerm.related.map((relId) => {
                    const rel = GLOSSARY_INDEX[relId]
                    if (!rel) return null
                    return (
                      <li key={relId}>
                        <CButton
                          color="link"
                          className="p-0"
                          onClick={() => navigateTo(relId)}
                        >
                          {t(`terms.${relId}.title`)}
                        </CButton>
                      </li>
                    )
                  })}
                </ul>
              </>
            )}
          </>
        )}
      </CModalBody>
      <CModalFooter>
        <CButton color="secondary" onClick={closeGlossary}>
          {t('modal.closeAria')}
        </CButton>
      </CModalFooter>
    </CModal>
  )
}

export const GlossaryProvider = ({ children = null }) => {
  const [isOpen, setIsOpen] = useState(false)
  const [termId, setTermId] = useState(null)

  const openGlossary = useCallback((id) => {
    setTermId(id || null)
    setIsOpen(true)
  }, [])

  const closeGlossary = useCallback(() => {
    setIsOpen(false)
  }, [])

  const navigateTo = useCallback((id) => {
    setTermId(id || null)
  }, [])

  const value = useMemo(
    () => ({ openGlossary, closeGlossary, isOpen, termId, navigateTo }),
    [openGlossary, closeGlossary, isOpen, termId, navigateTo],
  )

  return (
    <GlossaryContext.Provider value={value}>
      {children}
      <GlossaryModal />
    </GlossaryContext.Provider>
  )
}

GlossaryProvider.propTypes = {
  children: PropTypes.node,
}

export default GlossaryProvider
