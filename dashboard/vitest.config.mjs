// Sprint 6: minimal Vitest setup, separated from vite.config.mjs so the
// production bundle doesn't pull in jsdom or test-only deps. Coverage
// is intentionally limited to the new DSL editor surface - full
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
      // Sprint 5 (CRUD management): the admin views (games/tasks/users)
      // ship integration tests too.
      'src/views/admin/**/*.test.{js,jsx}',
      'src/i18n/**/*.test.js',
      'src/utils/**/*.test.js',
      'src/components/**/*.test.{js,jsx}',
      // Sprint 6 (CRUD management): the shared API client lives at the src
      // root, so its helper tests need their own top-level glob.
      'src/*.test.{js,jsx}',
    ],
    // Honest, whole-tree coverage: measure every source file under src/ (not
    // just the ones that happen to import a tested module) so the baseline
    // reflects how much of the frontend is actually exercised. Thresholds are
    // pinned to the measured baseline so coverage can't regress.
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov'],
      reportsDirectory: './coverage',
      include: ['src/**/*.{js,jsx}'],
      exclude: ['src/**/*.test.{js,jsx}', 'src/test-setup.js'],
      // Still emit the report when a test fails, otherwise a single red test
      // hides the coverage signal in CI.
      reportOnFailure: true,
      // Floors pinned just below the measured baseline (lines 45.62 / stmts
      // 44.19 / funcs 36.42 / branches 36.62 as of this sprint). The build
      // fails if coverage drops below them, so new code can't silently erode
      // the frontend's test net. Ratchet these up as coverage grows.
      thresholds: {
        lines: 45,
        statements: 44,
        functions: 36,
        branches: 36,
      },
    },
  },
})
