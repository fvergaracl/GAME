// React-joyride onboarding tour for the strategy editor.
//
// Thin wrapper over the generic OnboardingTour: it only owns the editor's
// localStorage key and step list and delegates the auto-trigger / locale /
// Joyride plumbing to the shared component instead of reimplementing it.
//
// Steps target ``data-tour="<name>"`` selectors so the StrategyEditor JSX
// can be restructured freely as long as the data-attributes survive -
// CSS-class selectors would be brittle against the dashboard's Bootstrap
// theme overrides.

import React, { useMemo } from 'react'
import PropTypes from 'prop-types'

import OnboardingTour from './OnboardingTour'

export const TOUR_LOCALSTORAGE_KEY = 'gd-editor-tour-seen'

const TOUR_STEP_KEYS = [
  { target: '[data-tour="editor-name"]', i18n: 'name', placement: 'bottom' },
  { target: '[data-tour="editor-mode"]', i18n: 'mode', placement: 'bottom' },
  {
    target: '[data-tour="editor-workspace"]',
    i18n: 'workspace',
    placement: 'top',
    spotlightClicks: true,
  },
  { target: '[data-tour="editor-save"]', i18n: 'save', placement: 'top' },
  { target: '[data-tour="editor-simulate"]', i18n: 'simulate', placement: 'left' },
  { target: '[data-tour="editor-history"]', i18n: 'history', placement: 'top' },
]

const EditorTour = ({ runRequest = 'auto', onFinished = null, hasHistory = false }) => {
  // The history step's target only exists once the strategy has been saved;
  // drop it otherwise so OnboardingTour never stalls on a missing selector.
  const steps = useMemo(
    () => TOUR_STEP_KEYS.filter((s) => hasHistory || s.i18n !== 'history'),
    [hasHistory],
  )

  // The editor's tour copy lives directly under ``editor:tour.*`` (no view
  // prefix), and the welcome blurb is the first step's title.
  return (
    <OnboardingTour
      storageKey={TOUR_LOCALSTORAGE_KEY}
      steps={steps}
      i18nNamespace="editor"
      keyPrefix=""
      welcomeKey="welcome"
      runRequest={runRequest}
      onFinished={onFinished}
    />
  )
}

EditorTour.propTypes = {
  // 'auto' = run only if the localStorage flag is missing; 'manual' = always
  // run; null = don't run. Toggling between values restarts the tour.
  runRequest: PropTypes.oneOf(['auto', 'manual', null]),
  onFinished: PropTypes.func,
  // Whether the editor is showing the "Ver historial" button. The history
  // step is dropped when the button doesn't exist yet (e.g. brand-new draft)
  // so Joyride doesn't error out on a missing target.
  hasHistory: PropTypes.bool,
}

export default EditorTour
