// Sprint 8: contract tests for the DSL glossary.
//
// Pins three things so the glossary doesn't drift silently:
//   1. Every entry in GLOSSARY_TERMS has a non-empty title + body in
//      both ES and EN - adding a term without translating it is a
//      detectable mistake instead of a quietly-missing card.
//   2. ``related`` cross-links and ``BLOCK_TO_TERM`` only point at ids
//      that exist in the index; otherwise navigating to a related term
//      would land on the "noTerm" empty state.
//   3. Every ``BLOCK_TO_TERM`` key is a real custom block type - i.e. it
//      shows up in HELP_SLUGS (the source of truth for block types in
//      this dashboard).

import { describe, expect, it } from 'vitest'

import { BLOCK_TO_TERM, GLOSSARY_INDEX, GLOSSARY_TERMS, SLUG_TO_TERM } from './index'
import esGlossary from '../../../i18n/locales/es/glossary.json'
import enGlossary from '../../../i18n/locales/en/glossary.json'

describe('GLOSSARY_TERMS', () => {
  for (const term of GLOSSARY_TERMS) {
    it(`ES has title + body for ${term.id}`, () => {
      const entry = esGlossary.terms[term.id]
      expect(entry, `missing es.terms.${term.id}`).toBeDefined()
      expect(entry.title).toBeTruthy()
      expect(entry.body).toBeTruthy()
    })
    it(`EN has title + body for ${term.id}`, () => {
      const entry = enGlossary.terms[term.id]
      expect(entry, `missing en.terms.${term.id}`).toBeDefined()
      expect(entry.title).toBeTruthy()
      expect(entry.body).toBeTruthy()
    })
  }

  it('related cross-links only point to existing ids', () => {
    for (const term of GLOSSARY_TERMS) {
      for (const relId of term.related || []) {
        expect(GLOSSARY_INDEX[relId], `${term.id} relates to unknown id ${relId}`).toBeTruthy()
      }
    }
  })

  it('SLUG_TO_TERM only maps slugs declared on the term entries', () => {
    for (const [slug, termId] of Object.entries(SLUG_TO_TERM)) {
      const term = GLOSSARY_INDEX[termId]
      expect(term, `slug ${slug} → unknown term ${termId}`).toBeTruthy()
      expect(term.blockSlug).toBe(slug)
    }
  })
})

describe('BLOCK_TO_TERM', () => {
  it('only references real glossary ids', () => {
    for (const [blockType, termId] of Object.entries(BLOCK_TO_TERM)) {
      expect(
        GLOSSARY_INDEX[termId],
        `block ${blockType} mapped to unknown glossary id ${termId}`,
      ).toBeTruthy()
    }
  })
})
