// Flat config for ESLint 9+. Replaces the legacy ``.eslintrc.js`` which
// ESLint 9 no longer reads (eslintrc support was removed as the default).
//
// Mirrors the previous setup: eslint-plugin-react "recommended" +
// react-hooks "recommended" + Prettier integration, with the React
// version auto-detected. Prettier formatting options live in
// ``.prettierrc.js`` and are picked up automatically by
// eslint-plugin-prettier — no need to duplicate them here.
import react from 'eslint-plugin-react'
import reactHooks from 'eslint-plugin-react-hooks'
import prettierRecommended from 'eslint-plugin-prettier/recommended'

export default [
  {
    ignores: ['build/**', 'node_modules/**', 'public/**', 'coverage/**'],
  },
  react.configs.flat.recommended,
  // Keep the classic react-hooks ruleset (rules-of-hooks +
  // exhaustive-deps) that the old ``.eslintrc.js`` enabled via
  // ``plugin:react-hooks/recommended``. v7's ``recommended-latest`` also
  // ships the new React Compiler rules, which would be a large,
  // out-of-scope behaviour change for this dependency bump.
  {
    plugins: { 'react-hooks': reactHooks },
    rules: {
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',
    },
  },
  prettierRecommended,
  {
    settings: {
      react: { version: 'detect' },
    },
  },
]
