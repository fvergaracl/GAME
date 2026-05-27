import React, { Suspense } from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { CSpinner } from '@coreui/react'

import './scss/style.scss'

// Lazy-loaded so the initial bundle doesn't pull DefaultLayout +
// every view eagerly. The sidebar/header/content under DefaultLayout
// is the standard CoreUI shell that AppContent.js routes against
// using routes.js.
const DefaultLayout = React.lazy(() => import('./layout/DefaultLayout'))
// Quick API stays available as a standalone route at /quick-api for
// backward compatibility — before this commit it was the *only*
// thing rendered and at least one ops workflow likely bookmarked it.
const QuickApiDashboard = React.lazy(
  () => import('./views/quick-api/QuickApiDashboard'),
)

const App = () => (
  <BrowserRouter>
    <Suspense
      fallback={
        <div className="pt-3 text-center">
          <CSpinner color="primary" variant="grow" />
        </div>
      }
    >
      <Routes>
        {/* Standalone Quick API URL for the existing ops shortcut. */}
        <Route path="/quick-api" element={<QuickApiDashboard />} />
        {/* Everything else goes through the standard layout
            (sidebar + header + lazy-routed content from routes.js). */}
        <Route path="*" element={<DefaultLayout />} />
      </Routes>
    </Suspense>
  </BrowserRouter>
)

export default App
