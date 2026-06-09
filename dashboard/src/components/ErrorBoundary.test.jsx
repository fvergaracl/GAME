// Sprint 9 - ErrorBoundary unit tests. Verifies the boundary catches
// render errors, shows the recovery UI, and resets cleanly when the
// caller clicks "Reintentar".

import React, { useState } from 'react'
import PropTypes from 'prop-types'
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import ErrorBoundary from './ErrorBoundary'

// React logs caught errors to console.error during tests. Silence it so
// the test output isn't drowned in stack traces.
let consoleSpy
beforeEach(() => {
  consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
})
afterEach(() => {
  consoleSpy.mockRestore()
})

const Boom = ({ shouldThrow }) => {
  if (shouldThrow) throw new Error('boom!')
  return <div>healthy</div>
}

Boom.propTypes = { shouldThrow: PropTypes.bool }

describe('ErrorBoundary', () => {
  it('renders children when no error is thrown', () => {
    render(
      <ErrorBoundary section="t">
        <div>hello</div>
      </ErrorBoundary>,
    )
    expect(screen.getByText('hello')).toBeInTheDocument()
  })

  it('renders the default fallback when a child throws', () => {
    render(
      <ErrorBoundary section="t">
        <Boom shouldThrow />
      </ErrorBoundary>,
    )
    // Both the outer .gd-section-error and the inner CAlert carry the
    // alert role; one assertion that we have at least one suffices.
    expect(screen.getAllByRole('alert').length).toBeGreaterThan(0)
    expect(screen.getByText(/Algo ha fallado/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Reintentar/i })).toBeInTheDocument()
  })

  it('passes the error to a render-prop fallback', () => {
    render(
      <ErrorBoundary
        section="t"
        fallback={({ error, section }) => (
          <span>
            broken in {section}: {error.message}
          </span>
        )}
      >
        <Boom shouldThrow />
      </ErrorBoundary>,
    )
    expect(screen.getByText('broken in t: boom!')).toBeInTheDocument()
  })

  it('clears the error state and re-renders children on reset', () => {
    const Harness = () => {
      const [shouldThrow, setShouldThrow] = useState(true)
      return (
        <ErrorBoundary section="t" onReset={() => setShouldThrow(false)}>
          <Boom shouldThrow={shouldThrow} />
        </ErrorBoundary>
      )
    }
    render(<Harness />)
    // Both the outer .gd-section-error and the inner CAlert carry the
    // alert role; one assertion that we have at least one suffices.
    expect(screen.getAllByRole('alert').length).toBeGreaterThan(0)
    fireEvent.click(screen.getByRole('button', { name: /Reintentar/i }))
    expect(screen.getByText('healthy')).toBeInTheDocument()
  })

  it('logs the error via console.error', () => {
    render(
      <ErrorBoundary section="diag">
        <Boom shouldThrow />
      </ErrorBoundary>,
    )
    expect(consoleSpy).toHaveBeenCalledWith(
      '[ErrorBoundary:diag]',
      expect.any(Error),
      expect.any(String),
    )
  })
})
