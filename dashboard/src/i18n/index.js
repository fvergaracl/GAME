// I18next configuration for the dashboard.
//
// The dashboard ships with full Spanish + English bundles for the
// surfaces a game designer interacts with (strategy editor, block
// tooltips, interpreter error codes). Other surfaces (admin tables,
// existing CoreUI shell) stay in Spanish for now and will inherit
// translations as needed - i18next falls back to the key string when a
// translation is missing, which keeps untranslated screens readable.
//
// Language selection priority:
//   1. ``localStorage["gd-locale"]`` if the user explicitly switched
//      languages (the editor toolbar writes there).
//   2. ``navigator.language`` via i18next-browser-languagedetector when
//      no preference is recorded yet (so a fresh designer in es-ES sees
//      Spanish, a fresh one in en-US sees English).
//   3. Spanish fallback. The team is Spain-based and Spanish copy is
//      the source of truth for the editor - English is a translation,
//      not the canonical language.
//
// Blockly's locale messages (workspace/category UI) are loaded by
// ``applyBlocklyLocale`` in StrategyEditor.jsx - i18next only owns the
// React tree's strings. The two systems are kept in lockstep by the
// editor reacting to ``i18n.on('languageChanged', ...)``.

import i18n from 'i18next'
import LanguageDetector from 'i18next-browser-languagedetector'
import { initReactI18next } from 'react-i18next'

import esEditor from './locales/es/editor.json'
import esErrors from './locales/es/errors.json'
import esBlocks from './locales/es/blocks.json'
import esCommon from './locales/es/common.json'
import esApp from './locales/es/app.json'
import esStrategies from './locales/es/strategies.json'
import esDashboard from './locales/es/dashboard.json'
import esExports from './locales/es/exports.json'
import esApikeys from './locales/es/apikeys.json'
import esGlossary from './locales/es/glossary.json'
import esManagement from './locales/es/management.json'
import enEditor from './locales/en/editor.json'
import enErrors from './locales/en/errors.json'
import enBlocks from './locales/en/blocks.json'
import enCommon from './locales/en/common.json'
import enApp from './locales/en/app.json'
import enStrategies from './locales/en/strategies.json'
import enDashboard from './locales/en/dashboard.json'
import enExports from './locales/en/exports.json'
import enApikeys from './locales/en/apikeys.json'
import enGlossary from './locales/en/glossary.json'
import enManagement from './locales/en/management.json'

export const SUPPORTED_LANGUAGES = ['es', 'en']
export const LOCALSTORAGE_LANG_KEY = 'gd-locale'

const resources = {
  es: {
    editor: esEditor,
    errors: esErrors,
    blocks: esBlocks,
    common: esCommon,
    app: esApp,
    strategies: esStrategies,
    dashboard: esDashboard,
    exports: esExports,
    apikeys: esApikeys,
    glossary: esGlossary,
    management: esManagement,
  },
  en: {
    editor: enEditor,
    errors: enErrors,
    blocks: enBlocks,
    common: enCommon,
    app: enApp,
    strategies: enStrategies,
    dashboard: enDashboard,
    exports: enExports,
    apikeys: enApikeys,
    glossary: enGlossary,
    management: enManagement,
  },
}

// Initialise once per page load. We intentionally don't expose the
// promise - i18next renders synchronously after init when resources are
// inlined (no Suspense boundary required).
i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'es',
    supportedLngs: SUPPORTED_LANGUAGES,
    // ``editor`` is the default ns so unprefixed ``t('chooser.title')``
    // resolves against editor.json; the rest are addressed with an
    // explicit ``ns:key`` prefix (e.g. ``common:status.DRAFT``).
    ns: [
      'editor',
      'errors',
      'blocks',
      'common',
      'app',
      'strategies',
      'dashboard',
      'exports',
      'apikeys',
      'glossary',
      'management',
    ],
    defaultNS: 'editor',
    interpolation: {
      // CoreUI renders strings as text by default; we only inject HTML
      // (e.g. <code> in mockHint) via <Trans> so escaping stays safe.
      escapeValue: false,
    },
    detection: {
      order: ['localStorage', 'navigator'],
      lookupLocalStorage: LOCALSTORAGE_LANG_KEY,
      caches: ['localStorage'],
    },
    returnEmptyString: false,
  })

export default i18n
