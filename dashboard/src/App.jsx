import React, { Suspense } from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'

import './scss/style.scss'
import ErrorBoundary from './components/ErrorBoundary'
import { SkeletonCard } from './components/Skeleton'

// Lazy-loaded so the initial bundle doesn't pull DefaultLayout +
// every view eagerly. The sidebar/header/content under DefaultLayout
// is the standard CoreUI shell that AppContent.js routes against
// using routes.js.
const DefaultLayout = React.lazy(() => import('./layout/DefaultLayout'))
// Quick API stays available as a standalone route at /quick-api for
// backward compatibility - before this commit it was the *only*
// thing rendered and at least one ops workflow likely bookmarked it.
const QuickApiDashboard = React.lazy(() => import('./views/quick-api/QuickApiDashboard'))

// Sprint 9: a chunk-load failure (deploy mid-session, network blip) used
// to crash the whole tree because no error boundary wrapped the top-
// level Suspense. Now an outer ErrorBoundary catches it and offers a
// reload, keeping the URL navigable.
const App = () => (
  <BrowserRouter>
    <ErrorBoundary section="App">
      <Suspense fallback={<SkeletonCard lines={5} />}>
        <Routes>
          {/* Standalone Quick API URL for the existing ops shortcut. */}
          <Route path="/quick-api" element={<QuickApiDashboard />} />
          {/* Everything else goes through the standard layout
              (sidebar + header + lazy-routed content from routes.js). */}
          <Route path="*" element={<DefaultLayout />} />
        </Routes>
      </Suspense>
    </ErrorBoundary>
  </BrowserRouter>
)

export default App
