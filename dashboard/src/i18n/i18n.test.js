// Sprint 10: contract tests for the i18n surface.
//
// The dashboard ships ES + EN bundles for ``editor``, ``errors`` and
// ``blocks``. These tests pin three things:
//
//   1. Every DSL error code we expect the backend to emit has a non-
//      empty translation in both locales — drift between backend codes
//      and frontend bundles is otherwise silent.
//   2. ``dslErrorMessage`` falls back to the generic ``errors.fallback``
//      template when the code isn't translated, so the user always sees
//      a sentence (never the bare DSL_* identifier).
//   3. ``translateDslError`` extracts the structured ``{code, params}``
//      from axios errors and from bare detail bodies — both shapes
//      reach the editor in practice.

import { describe, expect, it } from 'vitest'
import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

import { DSL_ERROR_CODES, dslErrorMessage } from './errorCodes'
import { translateDslError } from './errorMap'
import esEditor from './locales/es/editor.json'
import esErrors from './locales/es/errors.json'
import esBlocks from './locales/es/blocks.json'
import enEditor from './locales/en/editor.json'
import enErrors from './locales/en/errors.json'
import enBlocks from './locales/en/blocks.json'

// Initialise a fresh i18n instance synchronously so tests don't depend
// on the global one in src/i18n/index.js (which calls LanguageDetector
// and reads from window.localStorage — not available the same way
// inside vitest's jsdom env between test files).
async function setupI18n(lng) {
  await i18n.use(initReactI18next).init({
    resources: {
      es: { editor: esEditor, errors: esErrors, blocks: esBlocks },
      en: { editor: enEditor, errors: enErrors, blocks: enBlocks },
    },
    lng,
    fallbackLng: 'es',
    ns: ['editor', 'errors', 'blocks'],
    defaultNS: 'editor',
    interpolation: { escapeValue: false },
  })
  return i18n.t.bind(i18n)
}

describe('DSL error code translations', () => {
  for (const code of DSL_ERROR_CODES) {
    it(`ES has a translation for ${code}`, async () => {
      const t = await setupI18n('es')
      const out = t(`errors:${code}`, { defaultValue: '' })
      expect(out).toBeTruthy()
      expect(out).not.toBe(code)
    })
    it(`EN has a translation for ${code}`, async () => {
      const t = await setupI18n('en')
      const out = t(`errors:${code}`, { defaultValue: '' })
      expect(out).toBeTruthy()
      expect(out).not.toBe(code)
    })
  }
})

describe('dslErrorMessage fallbacks', () => {
  it('uses the generic errors.fallback when the code is unknown', async () => {
    const t = await setupI18n('es')
    const out = dslErrorMessage(t, 'DSL_TOTALLY_UNKNOWN_CODE', {}, 'raw english')
    expect(out).toContain('raw english')
    // Shouldn't leak the raw code identifier into the visible message.
    expect(out).not.toContain('DSL_TOTALLY_UNKNOWN_CODE')
  })

  it('interpolates params for a known code', async () => {
    const t = await setupI18n('en')
    const out = dslErrorMessage(
      t,
      'DSL_ARITH_DIV_BY_ZERO',
      { nodeId: 'r1.assign_points.0' },
      'division by zero',
    )
    expect(out).toContain('r1.assign_points.0')
  })
})

describe('translateDslError input shapes', () => {
  it('handles axios-shaped errors with structured detail', async () => {
    const t = await setupI18n('es')
    const axiosErr = {
      response: {
        data: {
          detail: {
            code: 'DSL_ARITH_DIV_BY_ZERO',
            params: { nodeId: 'n1' },
            message: 'division by zero',
          },
        },
      },
    }
    const out = translateDslError(t, axiosErr)
    expect(out).toContain('División por cero')
    expect(out).toContain('n1')
  })

  it('handles a bare string detail (legacy)', async () => {
    const t = await setupI18n('es')
    const out = translateDslError(t, {
      response: { data: { detail: 'legacy message' } },
    })
    expect(out).toBe('legacy message')
  })

  it('returns null when there is no DSL signal at all', async () => {
    const t = await setupI18n('es')
    expect(translateDslError(t, null)).toBeNull()
    expect(translateDslError(t, {})).toBeNull()
    expect(translateDslError(t, { foo: 'bar' })).toBeNull()
  })
})
