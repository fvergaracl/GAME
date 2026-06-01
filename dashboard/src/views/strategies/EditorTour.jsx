// Sprint 10: react-joyride onboarding tour for the strategy editor.
//
// Triggers once per browser unless the user manually clicks "Show tour
// again" in the toolbar. A localStorage flag (``gd-editor-tour-seen``)
// records that the tour has run so the next visit goes straight to the
// chooser without a popup.
//
// The tour targets ``data-tour="<name>"`` selectors so the StrategyEditor
// JSX is free to restructure as long as the data-attributes survive —
// CSS-class selectors would be brittle against the dashboard's Bootstrap
// theme overrides.

import React, { useCallback, useEffect, useMemo, useState } from 'react'
import PropTypes from 'prop-types'
import Joyride, { ACTIONS, EVENTS, STATUS } from 'react-joyride'
import { useTranslation } from 'react-i18next'

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
  {
    target: '[data-tour="editor-simulate"]',
    i18n: 'simulate',
    placement: 'left',
  },
  {
    target: '[data-tour="editor-history"]',
    i18n: 'history',
    placement: 'top',
  },
]

const EditorTour = ({ runRequest, onFinished, hasHistory }) => {
  const { t } = useTranslation('editor')
  const [run, setRun] = useState(false)
  const [stepIndex, setStepIndex] = useState(0)

  // Decide whether to start the tour on mount. The chooser screen
  // doesn't carry any of the tour targets so we only fire when the
  // editor is actually mounted (callers gate with stage==='editing').
  useEffect(() => {
    if (runRequest === 'manual') {
      setStepIndex(0)
      setRun(true)
      return
    }
    if (runRequest === 'auto') {
      const seen = window.localStorage.getItem(TOUR_LOCALSTORAGE_KEY)
      if (!seen) {
        setStepIndex(0)
        setRun(true)
      }
    }
  }, [runRequest])

  const steps = useMemo(() => {
    return TOUR_STEP_KEYS.filter((s) => hasHistory || s.i18n !== 'history').map((s) => ({
      target: s.target,
      placement: s.placement,
      content: t(`tour.steps.${s.i18n}`),
      // Welcome on the first step so it has a leading paragraph
      // instead of jumping straight into the form.
      title: s.i18n === 'name' ? t('tour.steps.welcome') : undefined,
      disableBeacon: s.i18n === 'name',
      spotlightClicks: s.spotlightClicks ?? false,
    }))
  }, [t, hasHistory])

  const locale = useMemo(
    () => ({
      back: t('tour.back'),
      close: t('tour.skip'),
      last: t('tour.last'),
      next: t('tour.next'),
      skip: t('tour.skip'),
    }),
    [t],
  )

  const handleCallback = useCallback(
    (data) => {
      const { action, index, status, type } = data
      if (type === EVENTS.STEP_AFTER || type === EVENTS.TARGET_NOT_FOUND) {
        // Move on when the user clicks next/skip OR when the step's
        // target isn't on screen — better to advance than freeze.
        setStepIndex(index + (action === ACTIONS.PREV ? -1 : 1))
        return
      }
      if (status === STATUS.FINISHED || status === STATUS.SKIPPED || action === ACTIONS.CLOSE) {
        setRun(false)
        setStepIndex(0)
        window.localStorage.setItem(TOUR_LOCALSTORAGE_KEY, '1')
        if (onFinished) onFinished()
      }
    },
    [onFinished],
  )

  return (
    <Joyride
      run={run}
      stepIndex={stepIndex}
      steps={steps}
      continuous
      showSkipButton
      showProgress
      disableScrolling={false}
      callback={handleCallback}
      locale={locale}
      styles={{
        // Sprint 9: same dark-mode-friendly token-driven palette as
        // OnboardingTour — the colour is no longer hardcoded.
        options: {
          zIndex: 10000,
          primaryColor: 'var(--cui-primary, #321fdb)',
          textColor: 'var(--cui-body-color, #1c1c1c)',
          backgroundColor: 'var(--cui-body-bg, #ffffff)',
          arrowColor: 'var(--cui-body-bg, #ffffff)',
        },
      }}
    />
  )
}

EditorTour.propTypes = {
  // 'auto' = run only if localStorage flag is missing; 'manual' = always
  // run; null = don't run. Toggling between values restarts the tour.
  runRequest: PropTypes.oneOf(['auto', 'manual', null]),
  onFinished: PropTypes.func,
  // Whether the editor is showing the "Ver historial" button. The
  // history step is skipped when the button doesn't exist yet (e.g.
  // brand-new draft) so Joyride doesn't error out on a missing target.
  hasHistory: PropTypes.bool,
}

EditorTour.defaultProps = {
  runRequest: 'auto',
  onFinished: null,
  hasHistory: false,
}

export default EditorTour
