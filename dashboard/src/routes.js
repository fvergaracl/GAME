import React from 'react'

const Dashboard = React.lazy(() => import('./views/dashboard/Dashboard'))

const Apikeys = React.lazy(() => import('./views/admin/apikeys/Apikeys'))
const ExportData = React.lazy(() => import('./views/exports/ExportData'))
const ExportHistory = React.lazy(() => import('./views/exports/ExportHistory'))
// Sprint 6: lazy-loaded so Blockly's ~1.5MB bundle is downloaded only
// when an admin actually opens the editor.
const StrategyEditor = React.lazy(() => import('./views/strategies/StrategyEditor'))
// Sprint 2: strategy library (discoverability). No Blockly dependency, so
// it stays out of the editor's heavy chunk.
const StrategyLibraryView = React.lazy(() => import('./views/strategies/StrategyLibraryView'))
// Sprint 3 (fix C5): per-block reference docs, opened from the editor's
// right-click "Help". Lazy + Blockly-free so it loads instantly in the
// new tab without pulling the editor bundle.
const BlockHelpView = React.lazy(() => import('./views/strategies/BlockHelpView'))
// Sprint 9: assignments view doesn't need Blockly but reuses the same
// lazy pattern to keep the assignments table out of the initial bundle.
const StrategyAssignmentsView = React.lazy(
  () => import('./views/strategies/StrategyAssignmentsView'),
)
// Sprint 10: observability + A/B comparison views. Both render
// aggregations from the sampled execution log and don't depend on
// Blockly, so they stay in their own small chunks.
const StrategyObservabilityView = React.lazy(
  () => import('./views/strategies/StrategyObservabilityView'),
)
const StrategyComparisonView = React.lazy(() => import('./views/strategies/StrategyComparisonView'))

const routes = [
  { path: '/', exact: true, name: 'Home' },
  { path: '/dashboard', name: 'Dashboard', element: Dashboard },
  { path: '/admin/api-keys', name: 'API keys', element: Apikeys },
  { path: '/admin/exports', name: 'Data export', element: ExportData },
  { path: '/admin/exports/history', name: 'Export history', element: ExportHistory },
  { path: '/strategies/library', name: 'My Strategies', element: StrategyLibraryView },
  { path: '/strategies/blocks-help/:slug', name: 'Block Help', element: BlockHelpView },
  { path: '/strategies/editor', name: 'Strategy Editor', element: StrategyEditor },
  { path: '/strategies/editor/:id', name: 'Edit Strategy', element: StrategyEditor },
  {
    path: '/admin/strategies/assignments',
    name: 'Strategy Assignments',
    element: StrategyAssignmentsView,
  },
  {
    path: '/strategies/observability',
    name: 'Strategy Observability',
    element: StrategyObservabilityView,
  },
  {
    path: '/strategies/compare',
    name: 'Strategy Comparison',
    element: StrategyComparisonView,
  },
]

export default routes
