// Sprint 1 (CRUD management) - create / edit a Game.
//
// Mirrors the react-hook-form + CForm + CFormFeedback pattern from
// ApikeysCreation, but rendered inside a CModal so the same component
// serves both "Nuevo juego" (create) and the per-row "Editar" action.
//
// Field shapes follow the backend schemas (PostCreateGame / PatchGame):
//   externalGameId (req, slug 3–60), platform (req), strategyId (opt,
//   default "default"), params (list of {key, value}).
//
// Two backend constraints shape the edit path:
//   1. PATCH /games only *updates* existing params (UpdateGameParams
//      requires an id); it can't create new ones. So on edit we send only
//      id-bearing params and surface a note explaining the limitation.
//   2. PATCH rejects a no-op update with 409; we let extractError surface
//      that message rather than pre-diffing client-side.

import React, { useEffect, useMemo, useState } from 'react'
import PropTypes from 'prop-types'
import { useForm } from 'react-hook-form'
import { useTranslation } from 'react-i18next'
import {
  CAlert,
  CButton,
  CForm,
  CFormFeedback,
  CFormInput,
  CFormLabel,
  CFormSelect,
  CFormText,
  CModal,
  CModalBody,
  CModalFooter,
  CModalHeader,
  CModalTitle,
  CSpinner,
} from '@coreui/react'

import {
  createGame,
  getGame,
  listBuiltInStrategies,
  listCustomStrategies,
  updateGame,
} from '../../../api'
import { extractError } from '../../../utils/errors'
import { useToast } from '../../../components/Toast'
import ParamsEditor from '../../../components/ParamsEditor'
import useUnsavedGuard from '../../../components/useUnsavedGuard'

// Suggested platforms for the select. The backend stores a free string,
// so this is just a convenience list - an existing game on an off-list
// platform keeps its value (we inject it as an extra option in edit mode).
export const PLATFORM_PRESETS = ['web', 'mobile', 'ios', 'android', 'desktop']

// Slug rule mirrors backend ``is_valid_slug``: ^[a-z0-9_-]{3,60}$ (i-flag).
const SLUG_PATTERN = /^[a-zA-Z0-9_-]{3,60}$/

// Backend params accept str | int | float | bool. The form edits everything
// as text, so on submit we re-narrow obvious numbers/booleans to keep a
// "10" param numeric instead of silently turning it into the string "10".
const coerceValue = (raw) => {
  if (typeof raw !== 'string') return raw
  const s = raw.trim()
  if (s === '') return ''
  if (s === 'true') return true
  if (s === 'false') return false
  if (/^-?\d+$/.test(s)) return Number(s)
  if (/^-?\d*\.\d+$/.test(s)) return Number(s)
  return raw
}

const buildStrategyOptions = (builtIns, customs, currentValue) => {
  const options = []
  const seen = new Set()
  for (const row of builtIns || []) {
    if (!row?.id || seen.has(row.id)) continue
    options.push({ value: row.id, label: row.name || row.id })
    seen.add(row.id)
  }
  for (const row of customs || []) {
    if (!row?.id) continue
    const value = `custom:${row.id}`
    if (seen.has(value)) continue
    options.push({ value, label: `${row.name} v${row.version}` })
    seen.add(value)
  }
  // Guarantee "default" is always selectable even if the built-in list
  // failed to load.
  if (!seen.has('default')) {
    options.unshift({ value: 'default', label: 'default' })
    seen.add('default')
  }
  // Preserve whatever the game already points at (e.g. an archived custom)
  // so editing doesn't silently reassign it.
  if (currentValue && !seen.has(currentValue)) {
    options.push({ value: currentValue, label: currentValue })
  }
  return options
}

const GameFormModal = ({ visible, mode, gameId, onClose, onSaved }) => {
  const { t } = useTranslation('management')
  const toast = useToast()

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting, isDirty },
  } = useForm({
    defaultValues: { externalGameId: '', platform: PLATFORM_PRESETS[0], strategyId: 'default' },
  })

  const [params, setParams] = useState([])
  // ParamsEditor lives outside react-hook-form, so its edits don't show up in
  // ``isDirty``. Track them separately for the unsaved-changes guard; the load
  // effect re-seeds params via setParams directly (not through this handler),
  // so loading a game for edit never trips the dirty flag.
  const [paramsDirty, setParamsDirty] = useState(false)
  const handleParamsChange = (next) => {
    setParamsDirty(true)
    setParams(next)
  }
  const [strategyOptions, setStrategyOptions] = useState([])
  const [platformOptions, setPlatformOptions] = useState(PLATFORM_PRESETS)
  const [loadingDetail, setLoadingDetail] = useState(false)
  const [formError, setFormError] = useState(null)

  const isEdit = mode === 'edit'

  // On open: load the strategy picklist (built-ins + published customs) and,
  // for edit, the game itself - then seed the form. Strategy-list failures
  // degrade gracefully (we still get "default"); a game fetch failure is
  // surfaced as a blocking error.
  useEffect(() => {
    if (!visible) return undefined
    let cancelled = false
    setFormError(null)
    setParamsDirty(false)
    setLoadingDetail(true)

    Promise.all([
      listBuiltInStrategies().catch(() => []),
      listCustomStrategies({ status: 'PUBLISHED' }).catch(() => []),
      isEdit && gameId ? getGame(gameId) : Promise.resolve(null),
    ])
      .then(([builtIns, customs, game]) => {
        if (cancelled) return
        const current = game?.strategyId || 'default'
        setStrategyOptions(buildStrategyOptions(builtIns, customs, current))

        if (isEdit && game) {
          const plats = [...PLATFORM_PRESETS]
          if (game.platform && !plats.includes(game.platform)) plats.unshift(game.platform)
          setPlatformOptions(plats)
          reset({
            externalGameId: game.externalGameId || '',
            platform: game.platform || PLATFORM_PRESETS[0],
            strategyId: game.strategyId || 'default',
          })
          setParams(
            (game.params || []).map((p) => ({
              id: p.id,
              key: p.key ?? '',
              value: p.value == null ? '' : String(p.value),
            })),
          )
        } else {
          setPlatformOptions([...PLATFORM_PRESETS])
          reset({ externalGameId: '', platform: PLATFORM_PRESETS[0], strategyId: 'default' })
          setParams([])
        }
      })
      .catch((err) => {
        if (!cancelled) setFormError(extractError(err, t('common.loadError')))
      })
      .finally(() => {
        if (!cancelled) setLoadingDetail(false)
      })

    return () => {
      cancelled = true
    }
  }, [visible, isEdit, gameId, reset, t])

  const cleanedParams = useMemo(
    () =>
      params
        .map((p) => ({ ...p, key: (p.key || '').trim() }))
        .filter((p) => p.key.length > 0),
    [params],
  )

  const onSubmit = async (values) => {
    setFormError(null)
    const base = {
      externalGameId: values.externalGameId.trim(),
      platform: values.platform,
      strategyId: values.strategyId || 'default',
    }
    try {
      if (isEdit) {
        // PATCH can only update existing params (needs id); new rows can't
        // be persisted here, so they're intentionally dropped.
        const updateParams = cleanedParams
          .filter((p) => p.id)
          .map((p) => ({ id: p.id, key: p.key, value: coerceValue(p.value) }))
        const payload = { ...base }
        if (updateParams.length) payload.params = updateParams
        await updateGame(gameId, payload)
        toast.success(t('feedback.gameUpdated'))
      } else {
        const createParams = cleanedParams.map((p) => ({ key: p.key, value: coerceValue(p.value) }))
        const payload = { ...base }
        if (createParams.length) payload.params = createParams
        await createGame(payload)
        toast.success(t('feedback.gameCreated'))
      }
      onSaved?.()
      onClose?.()
    } catch (err) {
      const msg = extractError(err, t('common.loadError'))
      setFormError(msg)
      toast.error(msg)
    }
  }

  const busy = isSubmitting || loadingDetail

  const handleClose = useUnsavedGuard({
    dirty: isDirty || paramsDirty,
    blocked: busy,
    onClose,
  })

  return (
    <CModal visible={visible} onClose={handleClose} size="lg" backdrop="static">
      <CModalHeader closeButton={!busy}>
        <CModalTitle>{isEdit ? t('games.editTitle') : t('games.createTitle')}</CModalTitle>
      </CModalHeader>
      <CForm onSubmit={handleSubmit(onSubmit)}>
        <CModalBody>
          {formError && <CAlert color="danger">{formError}</CAlert>}

          {loadingDetail ? (
            <div className="d-flex align-items-center gap-2 py-4 justify-content-center text-medium-emphasis">
              <CSpinner size="sm" /> {t('common:loading')}
            </div>
          ) : (
            <>
              <div className="mb-3">
                <CFormLabel htmlFor="game-externalGameId">
                  {t('games.form.externalGameId')}
                </CFormLabel>
                <CFormInput
                  id="game-externalGameId"
                  type="text"
                  placeholder="game-readme-001"
                  invalid={!!errors.externalGameId}
                  {...register('externalGameId', {
                    required: t('common.required'),
                    pattern: {
                      value: SLUG_PATTERN,
                      message: t('games.form.externalGameIdInvalid'),
                    },
                  })}
                />
                {errors.externalGameId ? (
                  <CFormFeedback invalid>{errors.externalGameId.message}</CFormFeedback>
                ) : (
                  <CFormText>{t('games.form.externalGameIdHelp')}</CFormText>
                )}
              </div>

              <div className="mb-3">
                <CFormLabel htmlFor="game-platform">{t('games.form.platform')}</CFormLabel>
                <CFormSelect
                  id="game-platform"
                  invalid={!!errors.platform}
                  {...register('platform', { required: t('common.required') })}
                >
                  {platformOptions.map((p) => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                </CFormSelect>
                {errors.platform && (
                  <CFormFeedback invalid>{errors.platform.message}</CFormFeedback>
                )}
              </div>

              <div className="mb-3">
                <CFormLabel htmlFor="game-strategyId">{t('games.form.strategyId')}</CFormLabel>
                <CFormSelect id="game-strategyId" {...register('strategyId')}>
                  {strategyOptions.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </CFormSelect>
              </div>

              <div className="mb-2">
                <CFormLabel>{t('games.form.params')}</CFormLabel>
                <ParamsEditor value={params} onChange={handleParamsChange} disabled={isSubmitting} />
                {isEdit && (
                  <CFormText>{t('games.form.paramsEditNote')}</CFormText>
                )}
              </div>
            </>
          )}
        </CModalBody>
        <CModalFooter>
          <CButton color="secondary" variant="outline" onClick={handleClose} disabled={busy}>
            {t('actions.cancel')}
          </CButton>
          <CButton color="primary" type="submit" disabled={busy}>
            {isSubmitting && <CSpinner size="sm" className="me-2" />}
            {isSubmitting ? t('actions.saving') : t('actions.save')}
          </CButton>
        </CModalFooter>
      </CForm>
    </CModal>
  )
}

GameFormModal.propTypes = {
  visible: PropTypes.bool.isRequired,
  mode: PropTypes.oneOf(['create', 'edit']).isRequired,
  gameId: PropTypes.string,
  onClose: PropTypes.func.isRequired,
  onSaved: PropTypes.func,
}

export default GameFormModal
