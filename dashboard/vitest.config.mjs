// Sprint 6: minimal Vitest setup, separated from vite.config.mjs so the
// production bundle doesn't pull in jsdom or test-only deps. Coverage
// is intentionally limited to the new DSL editor surface — full
// frontend test coverage is deferred to a later sprint.

import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      src: fileURLToPath(new URL('./src', import.meta.url)),
      '@utils': fileURLToPath(new URL('./src/utils', import.meta.url)),
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test-setup.js'],
    // Keep the matcher tight: the strategies editor surface (S6), the
    // i18n bundles (S10) and the Sprint 9 shared resilience primitives
    // (errors helper, Skeleton, ErrorBoundary) ship with tests. Sprint
    // 11 adds component/integration tests for the library + assignments
    // surfaces, hence the .jsx glob under views/strategies.
    include: [
      'src/views/strategies/**/*.test.{js,jsx}',
      'src/i18n/**/*.test.js',
      'src/utils/**/*.test.js',
      'src/components/**/*.test.{js,jsx}',
    ],
  },
})
