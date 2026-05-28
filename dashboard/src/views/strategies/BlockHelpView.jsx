// Sprint 3 (fix C5): renders a single block's reference documentation.
//
// Reached via Blockly's right-click "Help" (helpUrl =
// /strategies/blocks-help/:slug), which opens this in a new tab so the
// designer can read the docs side-by-side without losing editor state.
// The content is the real docs/dsl/blocks/<slug>.md bundled at build
// time (see blockDocs.js) — no duplication, no network fetch.
//
// We render the markdown source in a monospace block rather than pulling
// in a markdown renderer dependency: these docs are written with aligned
// tables and fenced code, so they stay perfectly readable as-is.
//
// Sprint 4: the field blocks additionally render a localised reference
// table of the whitelisted analytic paths (the "tabla de referencia" of
// the cryptic catalog). It's generated from the whitelist + i18n so it
// stays in sync with the dropdown and the backend mirror.

import React from 'react'
import { useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  CAlert,
  CCard,
  CCardBody,
  CCardHeader,
  CTable,
  CTableBody,
  CTableDataCell,
  CTableHead,
  CTableHeaderCell,
  CTableRow,
} from '@coreui/react'

import { getBlockDoc } from './blocks/blockDocs'
import { FIELD_PATHS, PARENT_FIELD_PATHS } from './dsl/whitelists'

// Which slugs get an auto-generated catalog table, and from which
// whitelist. ``field-data`` is intentionally absent: it reads an
// arbitrary ``data.<key>`` so there's no fixed catalog to list.
const FIELD_CATALOGS = {
  field: FIELD_PATHS,
  'field-parent': PARENT_FIELD_PATHS,
}

const BlockHelpView = () => {
  const { slug } = useParams()
  const { t } = useTranslation('blocks')
  const doc = getBlockDoc(slug)
  const catalogPaths = FIELD_CATALOGS[slug]

  return (
    <CCard className="mb-4">
      <CCardHeader>
        <strong>Ayuda del bloque</strong>
        {slug && <code className="ms-2">{slug}</code>}
      </CCardHeader>
      <CCardBody>
        {doc ? (
          <pre
            className="bg-body-tertiary p-3 rounded mb-0"
            style={{ whiteSpace: 'pre-wrap', fontSize: 13, lineHeight: 1.5 }}
          >
            {doc}
          </pre>
        ) : (
          <CAlert color="warning" className="mb-0">
            No hay documentación disponible para «{slug}».
          </CAlert>
        )}
        {catalogPaths && (
          <div className="mt-4">
            <h6>{t('fieldsTable.title')}</h6>
            <CTable small bordered responsive className="mb-0 align-middle">
              <CTableHead>
                <CTableRow>
                  <CTableHeaderCell>{t('fieldsTable.path')}</CTableHeaderCell>
                  <CTableHeaderCell>{t('fieldsTable.name')}</CTableHeaderCell>
                  <CTableHeaderCell>{t('fieldsTable.desc')}</CTableHeaderCell>
                </CTableRow>
              </CTableHead>
              <CTableBody>
                {catalogPaths.map((path) => (
                  <CTableRow key={path}>
                    <CTableDataCell>
                      <code>{path}</code>
                    </CTableDataCell>
                    <CTableDataCell>
                      {t(`fields.${path}.label`, { defaultValue: path })}
                    </CTableDataCell>
                    <CTableDataCell>
                      {t(`fields.${path}.desc`, { defaultValue: '' })}
                    </CTableDataCell>
                  </CTableRow>
                ))}
              </CTableBody>
            </CTable>
          </div>
        )}
      </CCardBody>
    </CCard>
  )
}

export default BlockHelpView
