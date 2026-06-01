import React from 'react'
import { AppContent, AppSidebar, AppFooter, AppHeader } from '../components/index'
import { GlossaryProvider } from '../views/strategies/glossary/GlossaryContext'

const DefaultLayout = () => {
  // Sprint 8: GlossaryProvider mounts a single shared modal at layout
  // level so any view (header help button, library row, editor badge…)
  // can openGlossary(term) without each one embedding its own modal.
  return (
    <GlossaryProvider>
      <div>
        <AppSidebar />
        <div className="wrapper d-flex flex-column min-vh-100">
          <AppHeader />
          <div className="body flex-grow-1">
            <AppContent />
          </div>
          <AppFooter />
        </div>
      </div>
    </GlossaryProvider>
  )
}

export default DefaultLayout
