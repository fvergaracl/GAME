import React, { Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { CContainer } from '@coreui/react'

import ErrorBoundary from './ErrorBoundary'
import { SkeletonCard } from './Skeleton'

const Page404 = React.lazy(() => import('../views/pages/page404/Page404'))

// routes config
import routes from '../routes'

// Sprint 9: each lazy-loaded route renders inside its own ErrorBoundary
// so a broken chunk or an unhandled render error in one view (e.g. the
// strategy editor failing to load Blockly) doesn't take the rest of the
// dashboard down. The Suspense fallback is a layout-preserving skeleton
// instead of an empty card with a spinner.
const AppContent = () => {
  return (
    <CContainer className="px-4" lg>
      <Suspense fallback={<SkeletonCard lines={4} />}>
        <Routes>
          {routes.map((route, idx) => {
            return (
              route.element && (
                <Route
                  key={idx}
                  path={route.path}
                  exact={route.exact}
                  name={route.name}
                  element={
                    <ErrorBoundary section={route.name || route.path}>
                      <route.element />
                    </ErrorBoundary>
                  }
                />
              )
            )
          })}
          <Route path="/" element={<Navigate to="dashboard" replace />} />
          <Route path="*" element={<Page404 />} />
        </Routes>
      </Suspense>
    </CContainer>
  )
}

export default React.memo(AppContent)
