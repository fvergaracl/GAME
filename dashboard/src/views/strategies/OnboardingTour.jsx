// Sprint 8: shared react-joyride wrapper for the Library and
// Assignments onboarding tours. Generalises the per-view-specific bits
// of EditorTour so we don't reimplement the same auto-trigger /
// localStorage / locale plumbing twice.
//
// Each consumer passes:
//   * a unique ``storageKey`` (one localStorage flag per tour),
//   * an i18n ``i18nNamespace`` + ``keyPrefix`` pair so the tour copy
//     can sit under e.g. ``strategies:library.tour.*`` (the i18next
//     ``strategies`` ns is shared across views; the prefix scopes per
//     view).
//   * the ``steps`` array - { target, placement, i18n, spotlightClicks? }
//     where ``i18n`` is the leaf under ``<keyPrefix>.steps.``.
//   * ``runRequest`` controlled by the parent: 'auto' on mount honours
//     the seen flag; 'manual' always runs; null stops.
//
// Skip-on-missing-target (TARGET_NOT_FOUND) advances rather than
// freezing - the same defensive behaviour EditorTour uses for the
// history step that only exists once a strategy has been saved.

import React, { useCallback, useEffect, useMemo, useState } from 'react'
import PropTypes from 'prop-types'
import { Joyride, ACTIONS, EVENTS, STATUS } from 'react-joyride'
import { useTranslation } from 'react-i18next'

const OnboardingTour = ({
  storageKey,
  steps,
  i18nNamespace,
  keyPrefix = '',
  welcomeKey = 'welcome',
  runRequest = 'auto',
  onFinished = null,
}) => {
  const { t } = useTranslation(i18nNamespace)
  const [run, setRun] = useState(false)
  const [stepIndex, setStepIndex] = useState(0)

  // ``keyPrefix`` is empty in the editor (lives at ``tour.*``) and
  // ``library.`` / ``assignments.`` in those views.
  const k = (suffix) => `${keyPrefix}${suffix}`

  useEffect(() => {
    if (runRequest === 'manual') {
      setStepIndex(0)
      setRun(true)
      return
    }
    if (runRequest === 'auto') {
      const seen = window.localStorage.getItem(storageKey)
      if (!seen) {
        setStepIndex(0)
        setRun(true)
      }
    }
  }, [runRequest, storageKey])

  const joyrideSteps = useMemo(() => {
    return steps.map((s, i) => ({
      target: s.target,
      placement: s.placement || 'auto',
      content: t(k(`tour.steps.${s.i18n}`)),
      title:
        i === 0 && welcomeKey
          ? t(k(`tour.steps.${welcomeKey}`), { defaultValue: '' }) || undefined
          : undefined,
      disableBeacon: i === 0,
      spotlightClicks: !!s.spotlightClicks,
    }))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [steps, t, welcomeKey, keyPrefix])

  const locale = useMemo(
    () => ({
      back: t(k('tour.back')),
      close: t(k('tour.skip')),
      last: t(k('tour.last')),
      next: t(k('tour.next')),
      skip: t(k('tour.skip')),
    }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [t, keyPrefix],
  )

  const handleCallback = useCallback(
    (data) => {
      const { action, index, status, type } = data
      if (type === EVENTS.STEP_AFTER || type === EVENTS.TARGET_NOT_FOUND) {
        setStepIndex(index + (action === ACTIONS.PREV ? -1 : 1))
        return
      }
      if (status === STATUS.FINISHED || status === STATUS.SKIPPED || action === ACTIONS.CLOSE) {
        setRun(false)
        setStepIndex(0)
        window.localStorage.setItem(storageKey, '1')
        if (onFinished) onFinished()
      }
    },
    [onFinished, storageKey],
  )

  return (
    <Joyride
      run={run}
      stepIndex={stepIndex}
      steps={joyrideSteps}
      continuous
      showSkipButton
      showProgress
      disableScrolling={false}
      callback={handleCallback}
      locale={locale}
      styles={{
        // Sprint 9: drive the tour off CoreUI tokens so dark mode and any
        // future theming stay in sync. Joyride consumes these as inline
        // styles, which accept ``var()`` values.
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

OnboardingTour.propTypes = {
  storageKey: PropTypes.string.isRequired,
  steps: PropTypes.arrayOf(
    PropTypes.shape({
      target: PropTypes.string.isRequired,
      placement: PropTypes.string,
      i18n: PropTypes.string.isRequired,
      spotlightClicks: PropTypes.bool,
    }),
  ).isRequired,
  i18nNamespace: PropTypes.string.isRequired,
  keyPrefix: PropTypes.string,
  welcomeKey: PropTypes.string,
  runRequest: PropTypes.oneOf(['auto', 'manual', null]),
  onFinished: PropTypes.func,
}

export default OnboardingTour
