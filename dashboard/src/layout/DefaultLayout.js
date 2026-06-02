import React from 'react'
import { AppContent, AppSidebar, AppFooter, AppHeader } from '../components/index'
import { ToastProvider } from '../components/Toast'
import { GlossaryProvider } from '../views/strategies/glossary/GlossaryContext'

const DefaultLayout = () => {
  // Sprint 8: GlossaryProvider mounts a single shared modal at layout
  // level so any view (header help button, library row, editor badge…)
  // can openGlossary(term) without each one embedding its own modal.
  // Sprint 11: ToastProvider does the same for feedback so every view
  // can call useToast() instead of reinventing CAlert plumbing.
  return (
    <ToastProvider>
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
    </ToastProvider>
  )
}

export default DefaultLayout
