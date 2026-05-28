import React from 'react'

const Dashboard = React.lazy(() => import('./views/dashboard/Dashboard'))

const Apikeys = React.lazy(() => import('./views/admin/apikeys/Apikeys'))
const ExportData = React.lazy(() => import('./views/exports/ExportData'))
const ExportHistory = React.lazy(() => import('./views/exports/ExportHistory'))
// Sprint 6: lazy-loaded so Blockly's ~1.5MB bundle is downloaded only
// when an admin actually opens the editor.
const StrategyEditor = React.lazy(() => import('./views/strategies/StrategyEditor'))
// Sprint 9: assignments view doesn't need Blockly but reuses the same
// lazy pattern to keep the assignments table out of the initial bundle.
const StrategyAssignmentsView = React.lazy(
  () => import('./views/strategies/StrategyAssignmentsView'),
)

const routes = [
  { path: '/', exact: true, name: 'Home' },
  { path: '/dashboard', name: 'Dashboard', element: Dashboard },
  { path: '/admin/api-keys', name: 'API keys', element: Apikeys },
  { path: '/admin/exports', name: 'Data export', element: ExportData },
  { path: '/admin/exports/history', name: 'Export history', element: ExportHistory },
  { path: '/strategies/editor', name: 'Strategy Editor', element: StrategyEditor },
  { path: '/strategies/editor/:id', name: 'Edit Strategy', element: StrategyEditor },
  {
    path: '/admin/strategies/assignments',
    name: 'Strategy Assignments',
    element: StrategyAssignmentsView,
  },
]

export default routes
