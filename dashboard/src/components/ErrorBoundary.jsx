// Section-level error boundary.
//
// React error boundaries are still class-only (no hook equivalent), so
// this is the one class component in the dashboard. Wraps a section
// (a route, the sidebar, a lazy chunk) so an unexpected render error
// or chunk-load failure is contained instead of tearing the whole
// dashboard down to a blank page.
//
// Usage:
//   <ErrorBoundary section="StrategyEditor">
//     <Suspense fallback={...}><StrategyEditor /></Suspense>
//   </ErrorBoundary>
//
// The fallback is intentionally minimal (a CAlert + a "Reintentar"
// button that resets the boundary). Recovery is best-effort: chunk-load
// failures usually need a full reload, so we offer that too.

import React from 'react'
import PropTypes from 'prop-types'
import { CAlert, CButton } from '@coreui/react'

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { error: null }
    this.handleReset = this.handleReset.bind(this)
    this.handleReload = this.handleReload.bind(this)
  }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, info) {
    // We don't have a remote logger wired in (the existing 40 print()
    // ports cited in mejoras.md cover the backend, not the dashboard).
    // ``console.error`` is the right escape hatch - it goes to the
    // browser devtools and to any in-page error overlay during dev.
    // eslint-disable-next-line no-console
    console.error(`[ErrorBoundary:${this.props.section || 'unknown'}]`, error, info?.componentStack)
  }

  handleReset() {
    this.setState({ error: null })
    if (typeof this.props.onReset === 'function') {
      try {
        this.props.onReset()
      } catch {
        // best-effort: a broken onReset shouldn't re-trip the boundary.
      }
    }
  }

  handleReload() {
    if (typeof window !== 'undefined') {
      window.location.reload()
    }
  }

  render() {
    const { error } = this.state
    if (!error) return this.props.children

    if (typeof this.props.fallback === 'function') {
      return this.props.fallback({
        error,
        reset: this.handleReset,
        section: this.props.section,
      })
    }

    const title = this.props.title || 'Algo ha fallado en esta sección.'
    const message =
      error?.message ||
      'No hemos podido renderizar este bloque. El resto del dashboard sigue funcionando.'

    return (
      <div className="gd-section-error" role="alert">
        <CAlert color="danger" className="mb-2">
          <strong>{title}</strong>
          <div className="small mt-1">{message}</div>
        </CAlert>
        <div className="d-flex gap-2">
          <CButton color="primary" size="sm" onClick={this.handleReset}>
            Reintentar
          </CButton>
          <CButton color="secondary" variant="outline" size="sm" onClick={this.handleReload}>
            Recargar la página
          </CButton>
        </div>
      </div>
    )
  }
}

ErrorBoundary.propTypes = {
  children: PropTypes.node,
  // Used in console diagnostics - pass the route/section name to
  // disambiguate when multiple boundaries are active.
  section: PropTypes.string,
  title: PropTypes.string,
  // Optional render-prop fallback. Receives ``{ error, reset, section }``.
  fallback: PropTypes.func,
  // Called after the user clicks "Reintentar". Use to re-fetch or
  // re-mount the wrapped subtree.
  onReset: PropTypes.func,
}

export default ErrorBoundary
