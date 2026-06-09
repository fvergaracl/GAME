// Sprint 9 - Skeleton primitives smoke tests. Verify the wrapper
// shapes render with the right classes and accessibility hints so the
// table/card skeletons stay drop-in replacements for spinners.

import React from 'react'
import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import Skeleton, { SkeletonCard, SkeletonTable, SkeletonText } from './Skeleton'

describe('Skeleton primitives', () => {
  it('renders a single skeleton with the expected class', () => {
    const { container } = render(<Skeleton ariaLabel="loading" />)
    const node = container.querySelector('.gd-skeleton')
    expect(node).not.toBeNull()
    expect(node.getAttribute('aria-busy')).toBe('true')
  })

  it('applies width/height via style', () => {
    const { container } = render(<Skeleton width={120} height="2rem" ariaLabel="x" />)
    const node = container.querySelector('.gd-skeleton')
    expect(node.style.width).toBe('120px')
    expect(node.style.height).toBe('2rem')
  })

  it('SkeletonText renders the requested number of bars', () => {
    const { container } = render(<SkeletonText lines={4} />)
    expect(container.querySelectorAll('.gd-skeleton').length).toBe(4)
  })

  it('SkeletonCard exposes a status role for screen readers', () => {
    render(<SkeletonCard lines={2} />)
    // Status role appears on the SkeletonCard and on each child Skeleton;
    // we just need to confirm at least one is present so AT picks it up.
    expect(screen.getAllByRole('status').length).toBeGreaterThan(0)
  })

  it('SkeletonTable renders rows × (columns + actions) cells', () => {
    const { container } = render(<SkeletonTable columns={3} rows={4} hasActions />)
    // 4 body rows + 1 header row; each row has 4 cells (3 + actions).
    const bodyRows = container.querySelectorAll('tbody tr')
    expect(bodyRows.length).toBe(4)
    expect(bodyRows[0].querySelectorAll('td').length).toBe(4)
    const headerCells = container.querySelectorAll('thead th')
    expect(headerCells.length).toBe(4)
  })
})
