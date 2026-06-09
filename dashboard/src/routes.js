import React from 'react'

const Dashboard = React.lazy(() => import('./views/dashboard/Dashboard'))

const Apikeys = React.lazy(() => import('./views/admin/apikeys/Apikeys'))
const ExportData = React.lazy(() => import('./views/exports/ExportData'))
const ExportHistory = React.lazy(() => import('./views/exports/ExportHistory'))
// Lazy-loaded so Blockly's ~1.5MB bundle is downloaded only
// when an admin actually opens the editor.
const StrategyEditor = React.lazy(() => import('./views/strategies/StrategyEditor'))
// Strategy library (discoverability). No Blockly dependency, so
// it stays out of the editor's heavy chunk.
const StrategyLibraryView = React.lazy(() => import('./views/strategies/StrategyLibraryView'))
// Per-block reference docs, opened from the editor's
// right-click "Help". Lazy + Blockly-free so it loads instantly in the
// new tab without pulling the editor bundle.
const BlockHelpView = React.lazy(() => import('./views/strategies/BlockHelpView'))
// Assignments view doesn't need Blockly but reuses the same
// lazy pattern to keep the assignments table out of the initial bundle.
const StrategyAssignmentsView = React.lazy(
  () => import('./views/strategies/StrategyAssignmentsView'),
)
// Observability + A/B comparison views. Both render
// aggregations from the sampled execution log and don't depend on
// Blockly, so they stay in their own small chunks.
const StrategyObservabilityView = React.lazy(
  () => import('./views/strategies/StrategyObservabilityView'),
)
const StrategyComparisonView = React.lazy(() => import('./views/strategies/StrategyComparisonView'))
// Games lifecycle admin. No Blockly dependency,
// so it stays in its own small chunk like the other admin tables.
const GamesManagementView = React.lazy(() => import('./views/admin/games/GamesManagementView'))
// Per-game task management (CRUD + duplicate +
// bulk create). Reached from a game row's "Ver tareas" action; keyed on the
// internal gameId so it can mutate tasks by their internal UUID.
const GameTasksView = React.lazy(() => import('./views/admin/games/GameTasksView'))
// Read-only Users explorer. Users aren't a real
// CRUD entity (rows are created implicitly), so this is a lookup-only view -
// search an externalUserId, see its points + wallet. No Blockly, own chunk.
const UsersExplorerView = React.lazy(() => import('./views/admin/users/UsersExplorerView'))

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
  { path: '/admin/games', name: 'Games', element: GamesManagementView },
  { path: '/admin/games/:gameId/tasks', name: 'Game Tasks', element: GameTasksView },
  { path: '/admin/users', name: 'Users', element: UsersExplorerView },
]

export default routes
