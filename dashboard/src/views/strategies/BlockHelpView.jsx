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

import React from 'react'
import { useParams } from 'react-router-dom'
import { CAlert, CCard, CCardBody, CCardHeader } from '@coreui/react'

import { getBlockDoc } from './blocks/blockDocs'

const BlockHelpView = () => {
  const { slug } = useParams()
  const doc = getBlockDoc(slug)

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
      </CCardBody>
    </CCard>
  )
}

export default BlockHelpView
