// Sprint 6: Strategy Editor view — embeds a Blockly workspace alongside
// a "Probar" simulate panel.
//
// Layout: two CCols (CoreUI Bootstrap grid). The editor takes 2/3 of the
// width, the simulate panel takes the right 1/3. Both are inside a CCard
// for visual consistency with the rest of the dashboard (ExportData,
// ApikeysCreation, etc.).
//
// State machine (intentionally simple — no Redux, no react-hook-form):
//   * Workspace is mutated imperatively via the Blockly API and held in a
//     ref. The React render tree never re-renders on every block drag.
//   * Save / Simulate buttons read the workspace once on click via the
//     generator, then dispatch the API call.
//   * Errors / success / last simulation result go through useState so
//     CAlert and the trace panel re-render reactively.

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Trans, useTranslation } from 'react-i18next'
import * as Blockly from 'blockly'
import * as BlocklyEsMsg from 'blockly/msg/es'
import * as BlocklyEnMsg from 'blockly/msg/en'
import {
  CAlert,
  CBadge,
  CButton,
  CCard,
  CCardBody,
  CCardHeader,
  CCardText,
  CCardTitle,
  CCol,
  CForm,
  CFormCheck,
  CFormInput,
  CFormLabel,
  CFormSelect,
  CFormTextarea,
  CRow,
  CSpinner,
} from '@coreui/react'

import {
  createCustomStrategy,
  getCustomStrategy,
  getStrategySchema,
  importCustomStrategy,
  listBuiltInStrategies,
  simulateCustomStrategy,
  updateCustomStrategy,
} from '../../api'
import keycloak from '../../keycloak'
import LanguageSwitcher from '../../components/LanguageSwitcher'
import { translateDslError } from '../../i18n/errorMap'
import {
  DEFAULT_TOOLBOX_XML,
  EXTEND_TOOLBOX_XML,
  STARTER_RULE_XML,
  refreshBlockI18n,
  registerDslBlocks,
} from './blocks'
import { workspaceToAst } from './dsl/generator'
import { validateAst } from './dsl/validator'
import EditorTour from './EditorTour'
import StrategyVersionHistoryModal from './StrategyVersionHistoryModal'
import TemplatePickerModal from './TemplatePickerModal'

// Sprint 10: feed Blockly's own UI strings (right-click menu, trash
// confirmations, etc.) the user's locale. Defaults to Spanish to match
// the rest of the editor; the language switcher swaps these messages
// in-place via `applyBlocklyLocale`.
const BLOCKLY_MSG_BY_LANG = { es: BlocklyEsMsg, en: BlocklyEnMsg }

function applyBlocklyLocale(lang) {
  const bundle = BLOCKLY_MSG_BY_LANG[lang] || BLOCKLY_MSG_BY_LANG.es
  // The compiled msg modules expose all keys on the default export.
  // Object.assign copies them into Blockly.Msg without disturbing
  // app-specific custom entries.
  Object.assign(Blockly.Msg, bundle.default || bundle)
}

// Inline admin-token decoder so the "Hacer rollback" CTA inside the
// history modal stays disabled for non-admins. The server-side
// ``require_admin`` gate is the authoritative check; this is just a
// UX hint to avoid showing a button that would always 403.
const isCurrentUserAdmin = () => {
  try {
    const token = keycloak?.token
    if (!token) return false
    const payload = token.split('.')[1]
    const decoded = JSON.parse(atob(payload))
    return (
      decoded?.resource_access?.account?.roles?.includes('AdministratorGAME') ||
      false
    )
  } catch {
    return false
  }
}

const INITIAL_SIM_FORM = {
  externalGameId: 'game-1',
  externalTaskId: 'task-1',
  externalUserId: 'user-1',
  dataJson: '{}',
  mockStateJson: '{\n  "task.measurements_count": 1\n}',
}

const StrategyEditor = () => {
  const { t, i18n } = useTranslation('editor')

  // Sprint 10: lock in the active language for Blockly's own UI
  // (right-click menus, trash dialog, etc.) and re-tooltip every
  // registered block in the active locale. Idempotent — re-running on
  // every language change is the supported pattern.
  useEffect(() => {
    applyBlocklyLocale(i18n.resolvedLanguage)
    registerDslBlocks(t)
    if (workspaceRef.current) {
      refreshBlockI18n(workspaceRef.current, t)
    }
  }, [t, i18n.resolvedLanguage])

  // Sprint 8: ``/strategies/editor/:id`` reuses the same component to
  // edit an existing strategy. When ``id`` is present we skip the
  // empty-state chooser and jump straight into editing mode after
  // loading the row from the backend.
  const { id: routeStrategyId } = useParams()
  const navigate = useNavigate()

  // Sprint 10: tour gating. ``runRequest=auto`` defers to the
  // localStorage flag inside EditorTour; flipping to ``manual`` from the
  // toolbar replays the tour on demand.
  const [tourRunRequest, setTourRunRequest] = useState('auto')

  const workspaceDivRef = useRef(null)
  const workspaceRef = useRef(null)
  // Sprint 7: parent schema is read by Blockly's toolbox callback,
  // which is registered ONCE per workspace lifecycle. The callback
  // closes over a ref so it always sees the latest schema without
  // forcing a workspace re-injection on every parent change.
  const parentSchemaRef = useRef(null)

  const [strategyName, setStrategyName] = useState('Mi estrategia')
  const [description, setDescription] = useState('')
  const [strategyId, setStrategyId] = useState(routeStrategyId || null)
  const [loadedVersion, setLoadedVersion] = useState(null)

  // Sprint 7: editor mode + parent metadata.
  const [mode, setMode] = useState('DSL_FULL')
  const [parentId, setParentId] = useState('')
  const [parentSchema, setParentSchema] = useState(null)
  const [builtIns, setBuiltIns] = useState([])
  const [parentLoadError, setParentLoadError] = useState(null)

  // Sprint 8: stage gates the empty-state chooser. 'editing' enters the
  // full Blockly workspace; 'chooser' shows three CTAs. We skip the
  // chooser when the route already names a strategy id.
  const [stage, setStage] = useState(routeStrategyId ? 'editing' : 'chooser')
  const [templateModalOpen, setTemplateModalOpen] = useState(false)
  const [pendingTemplate, setPendingTemplate] = useState(null)
  const [pendingImportBundle, setPendingImportBundle] = useState(null)
  // Sprint 11: queue a starter rule for the "Crear estrategia vacía"
  // path so the freshly-injected workspace lands on a valid example
  // instead of a blank canvas that fails validation on first save/test.
  const [pendingSeed, setPendingSeed] = useState(false)
  const [loadError, setLoadError] = useState(null)
  const fileInputRef = useRef(null)

  const [validationErrors, setValidationErrors] = useState([])
  const [saveError, setSaveError] = useState(null)
  const [saveSuccess, setSaveSuccess] = useState(null)
  const [isSaving, setIsSaving] = useState(false)
  const [isImporting, setIsImporting] = useState(false)

  const [simForm, setSimForm] = useState(INITIAL_SIM_FORM)
  const [simResult, setSimResult] = useState(null)
  const [simError, setSimError] = useState(null)
  const [isSimulating, setIsSimulating] = useState(false)

  // Sprint 9: history modal visibility. Only meaningful when the editor
  // is loaded with an existing strategy (i.e. ``strategyId`` is set);
  // otherwise there's no family to walk back through.
  const [historyOpen, setHistoryOpen] = useState(false)
  const isAdmin = useMemo(() => isCurrentUserAdmin(), [])

  // Sprint 7: toolbox swaps wholesale when the mode changes. We track
  // it as state (not just useMemo) because the Blockly workspace needs
  // to be re-injected when the toolbox changes — see the useEffect
  // dependency below.
  const toolboxXml = useMemo(
    () => (mode === 'DSL_EXTEND' ? EXTEND_TOOLBOX_XML : DEFAULT_TOOLBOX_XML),
    [mode],
  )

  // ----- Blockly workspace lifecycle ---------------------------------------
  // Sprint 8: the workspace only mounts when ``stage === 'editing'``.
  // While the chooser is showing, workspaceDivRef.current is null and
  // we skip injection entirely — no orphan Blockly instance hanging
  // around behind the chooser cards.
  useEffect(() => {
    if (stage !== 'editing') return
    if (!workspaceDivRef.current) return
    const workspace = Blockly.inject(workspaceDivRef.current, {
      toolbox: toolboxXml,
      trashcan: true,
      scrollbars: true,
      sounds: false,
      // Conservative zoom defaults — designers tend to over-zoom otherwise.
      zoom: { controls: true, wheel: true, startScale: 0.9 },
    })
    workspaceRef.current = workspace

    // Sprint 7: the "Overrides padre" toolbox category is populated
    // dynamically from the parent schema. Registering the callback
    // here means the workspace can read parentSchemaRef.current at the
    // moment the designer opens the category, so a schema change
    // doesn't require re-injecting the workspace.
    workspace.registerToolboxCategoryCallback('PARENT_OVERRIDES', (ws) =>
      _buildParentOverrideFlyout(ws, parentSchemaRef.current),
    )

    // Sprint 8: a template / imported bundle queued by the chooser is
    // hydrated AFTER the workspace exists. Doing it inside this effect
    // — instead of synchronously from the chooser handler — guarantees
    // workspaceRef.current is the freshly-injected instance, not a
    // stale one from a previous mount.
    if (pendingTemplate) {
      loadWorkspaceFromSerialized(workspace, pendingTemplate.blocklyXml)
      setPendingTemplate(null)
    } else if (pendingImportBundle) {
      loadWorkspaceFromSerialized(workspace, pendingImportBundle.blocklyXml)
      setPendingImportBundle(null)
    } else if (pendingSeed) {
      // Sprint 11: seed a valid starter rule for the from-scratch path.
      loadWorkspaceFromSerialized(workspace, STARTER_RULE_XML)
      setPendingSeed(false)
    }

    return () => {
      workspace.dispose()
      workspaceRef.current = null
    }
  }, [stage, toolboxXml, pendingTemplate, pendingImportBundle, pendingSeed])

  // ----- Load existing strategy by id (Sprint 8) ---------------------------
  // When the route carries an id we fetch the row, prime the editor's
  // name/description/mode fields, and queue the saved Blockly state for
  // hydration once the workspace mounts. The fetch only runs once per
  // id; subsequent edits stay in-memory until the user navigates away.
  useEffect(() => {
    if (!routeStrategyId) return
    let cancelled = false
    setLoadError(null)
    getCustomStrategy(routeStrategyId)
      .then((row) => {
        if (cancelled) return
        setStrategyId(row.id)
        setStrategyName(row.name || '')
        setDescription(row.description || '')
        setLoadedVersion(row.version ?? null)
        if (row.type === 'DSL_EXTEND' || row.type === 'DSL_FULL') {
          setMode(row.type)
        }
        if (row.parentStrategyId) {
          setParentId(row.parentStrategyId)
        }
        if (row.blocklyXml) {
          // Queue for the workspace effect to hydrate. Don't try to load
          // here — the workspace may not be mounted yet on first render.
          setPendingImportBundle({ blocklyXml: row.blocklyXml })
        }
      })
      .catch((err) => {
        if (!cancelled) setLoadError(translateDslError(t, err) || extractError(err, t))
      })
    return () => {
      cancelled = true
    }
  }, [routeStrategyId, t])

  // ----- Built-ins list (parent picker source) -----------------------------
  // Loaded once on mount. The list is small (~6 entries) so re-fetching
  // on demand isn't worth the complexity.
  useEffect(() => {
    let cancelled = false
    listBuiltInStrategies()
      .then((rows) => {
        if (!cancelled) setBuiltIns(Array.isArray(rows) ? rows : [])
      })
      .catch((err) => {
        if (!cancelled) {
          setParentLoadError(translateDslError(t, err) || extractError(err, t))
          setBuiltIns([])
        }
      })
    return () => {
      cancelled = true
    }
    // ``t`` is stable across renders so depending on it here is safe;
    // the ESLint exhaustive-deps rule still wants it listed for clarity.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [t])

  // ----- Parent schema fetch -----------------------------------------------
  // Re-runs whenever the designer picks a different parent. The result
  // feeds both the read-only side panel and the dynamic toolbox.
  useEffect(() => {
    if (mode !== 'DSL_EXTEND' || !parentId) {
      setParentSchema(null)
      parentSchemaRef.current = null
      return
    }
    let cancelled = false
    setParentLoadError(null)
    getStrategySchema(parentId)
      .then((schema) => {
        if (cancelled) return
        setParentSchema(schema)
        parentSchemaRef.current = schema
      })
      .catch((err) => {
        if (cancelled) return
        setParentLoadError(translateDslError(t, err) || extractError(err, t))
        setParentSchema(null)
        parentSchemaRef.current = null
      })
    return () => {
      cancelled = true
    }
  }, [mode, parentId, t])

  // ----- Chooser actions (Sprint 8) ----------------------------------------
  const startFromScratch = useCallback(() => {
    setMode('DSL_FULL')
    setParentId('')
    setPendingSeed(true)
    setStage('editing')
  }, [])

  const startFromExtend = useCallback(() => {
    setMode('DSL_EXTEND')
    setStage('editing')
  }, [])

  const handleTemplateSelected = useCallback((tpl) => {
    // Prime the editor with the template's metadata and queue the
    // Blockly XML for hydration once the workspace mounts. We don't
    // touch workspaceRef here — the workspace effect handles that
    // after Blockly.inject runs.
    setStrategyName(`${tpl.name} (copia)`)
    setDescription(tpl.description || '')
    setMode(tpl.type)
    setParentId(tpl.parentStrategyId || '')
    setPendingTemplate(tpl)
    setStrategyId(null)
    setLoadedVersion(null)
    setStage('editing')
  }, [])

  // ----- Import / Export JSON (Sprint 8) -----------------------------------
  const handleExport = useCallback(() => {
    if (!workspaceRef.current) {
      setSaveError(t('alerts.noWorkspace'))
      return
    }
    let ast
    try {
      ast = workspaceToAst(workspaceRef.current)
    } catch (err) {
      setSaveError(t('alerts.serializeFailed', { error: err.message }))
      return
    }
    // Persist Blockly's modern JSON state so a round-trip lands on the
    // exact same workspace shape — block positions and collapsed flags
    // included. The backend will accept this string in the blocklyXml
    // field; the loader (loadWorkspaceFromSerialized) sniffs the format
    // on the way back in.
    const blocklyState = Blockly.serialization.workspaces.save(workspaceRef.current)
    const bundle = {
      name: strategyName,
      description: description || null,
      type: mode,
      parentStrategyId: mode === 'DSL_EXTEND' ? parentId : null,
      astJson: ast,
      blocklyXml: JSON.stringify(blocklyState),
      exportedAt: new Date().toISOString(),
      exportedFromVersion: loadedVersion,
    }
    const blob = new Blob([JSON.stringify(bundle, null, 2)], {
      type: 'application/json',
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    const safeName =
      (strategyName || 'strategy').replace(/[^A-Za-z0-9_-]+/g, '_').slice(0, 60) || 'strategy'
    link.download = `${safeName}.json`
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  }, [strategyName, description, mode, parentId, loadedVersion])

  const handleImportFile = useCallback(
    async (file) => {
      setSaveError(null)
      setSaveSuccess(null)
      if (!file) return
      let bundle
      try {
        const text = await file.text()
        bundle = JSON.parse(text)
      } catch (err) {
        setSaveError(t('alerts.fileReadFailed', { error: err.message }))
        return
      }
      if (!bundle || typeof bundle !== 'object' || !bundle.astJson) {
        setSaveError(t('alerts.notAStrategyBundle'))
        return
      }
      setIsImporting(true)
      try {
        const created = await importCustomStrategy({
          name: bundle.name || 'Estrategia importada',
          description: bundle.description || null,
          type: bundle.type || 'DSL_FULL',
          parentStrategyId: bundle.parentStrategyId || null,
          astJson: bundle.astJson,
          blocklyXml: bundle.blocklyXml || '<xml></xml>',
          experimentTag: bundle.experimentTag || null,
          exportedAt: bundle.exportedAt,
          exportedFromVersion: bundle.exportedFromVersion,
        })
        // Land the user in /strategies/editor/:newId so the editor's
        // load-by-id effect picks up the freshly persisted draft and
        // hydrates the workspace from scratch — avoids edge cases where
        // a half-loaded workspace remains from the previous session.
        navigate(`/strategies/editor/${created.id}`)
      } catch (err) {
        setSaveError(translateDslError(t, err) || extractError(err, t))
      } finally {
        setIsImporting(false)
      }
    },
    [navigate, t],
  )

  // ----- Save (create or update) -------------------------------------------
  const buildAndValidateAst = useCallback(() => {
    if (!workspaceRef.current) return null
    const ast = workspaceToAst(workspaceRef.current)
    const result = validateAst(ast)
    if (!result.ok) {
      setValidationErrors(result.errors)
      highlightErrorBlocks(workspaceRef.current, result.errors, t)
      return null
    }
    setValidationErrors([])
    clearBlockWarnings(workspaceRef.current)
    return ast
  }, [t])

  const handleSave = useCallback(async () => {
    setSaveError(null)
    setSaveSuccess(null)
    const ast = buildAndValidateAst()
    if (!ast) return
    if (!strategyName.trim()) {
      setSaveError(t('alerts.nameRequired'))
      return
    }

    // Capture the Blockly serialised state so the editor can be
    // reopened on the same draft from the same workspace shape.
    const blocklyJson = Blockly.serialization.workspaces.save(workspaceRef.current)

    // Sprint 7: when the editor is in DSL_EXTEND mode the payload
    // carries the parent id; in DSL_FULL mode parentStrategyId is
    // explicitly null so the backend's _validate_payload rejects any
    // accidental mismatch.
    if (mode === 'DSL_EXTEND' && !parentId) {
      setSaveError(t('alerts.noParent'))
      return
    }
    const payload = {
      name: strategyName.trim(),
      description: description.trim() || null,
      type: mode,
      parentStrategyId: mode === 'DSL_EXTEND' ? parentId : null,
      astJson: ast,
      blocklyXml: JSON.stringify(blocklyJson),
    }

    setIsSaving(true)
    try {
      if (strategyId) {
        const updated = await updateCustomStrategy(strategyId, payload)
        // The backend forks PUBLISHED rows into a new DRAFT version+1;
        // grab whatever id came back so subsequent saves target it.
        setStrategyId(updated.id)
        setSaveSuccess(
          t('alerts.saveSuccessUpdate', {
            version: updated.version,
            status: updated.status,
          }),
        )
      } else {
        const created = await createCustomStrategy(payload)
        setStrategyId(created.id)
        setSaveSuccess(
          t('alerts.saveSuccessCreate', {
            id: created.id,
            version: created.version,
          }),
        )
      }
    } catch (err) {
      setSaveError(translateDslError(t, err) || extractError(err, t))
    } finally {
      setIsSaving(false)
    }
  }, [strategyName, description, strategyId, mode, parentId, buildAndValidateAst, t])

  // ----- Simulate ----------------------------------------------------------
  const handleSimulate = useCallback(async () => {
    setSimError(null)
    setSimResult(null)
    const ast = buildAndValidateAst()
    if (!ast) return

    let dataParsed
    let mockStateParsed
    try {
      dataParsed = simForm.dataJson ? JSON.parse(simForm.dataJson) : {}
    } catch (err) {
      setSimError(t('alerts.invalidDataJson', { error: err.message }))
      return
    }
    try {
      mockStateParsed = simForm.mockStateJson ? JSON.parse(simForm.mockStateJson) : {}
    } catch (err) {
      setSimError(t('alerts.invalidMockJson', { error: err.message }))
      return
    }

    // /simulate requires a persisted strategy id. If the designer hasn't
    // saved yet, persist as a hidden draft first so they can iterate
    // without remembering to click Save before Test.
    let targetId = strategyId
    if (!targetId) {
      try {
        if (mode === 'DSL_EXTEND' && !parentId) {
          setSimError(t('alerts.noParentSim'))
          return
        }
        const draft = await createCustomStrategy({
          name: strategyName.trim() || 'Borrador',
          description: description.trim() || null,
          type: mode,
          parentStrategyId: mode === 'DSL_EXTEND' ? parentId : null,
          astJson: ast,
          blocklyXml: null,
        })
        targetId = draft.id
        setStrategyId(targetId)
      } catch (err) {
        setSimError(translateDslError(t, err) || extractError(err, t))
        return
      }
    }

    setIsSimulating(true)
    try {
      const response = await simulateCustomStrategy(targetId, {
        externalGameId: simForm.externalGameId,
        externalTaskId: simForm.externalTaskId,
        externalUserId: simForm.externalUserId,
        data: dataParsed,
        mockState: mockStateParsed,
      })
      setSimResult(response)
    } catch (err) {
      setSimError(translateDslError(t, err) || extractError(err, t))
    } finally {
      setIsSimulating(false)
    }
  }, [buildAndValidateAst, simForm, strategyId, strategyName, description, mode, parentId, t])

  // ----- Render ------------------------------------------------------------
  // Sprint 8: render the empty-state chooser as a stand-alone card when
  // we don't have an id or an explicit user choice yet. The Blockly
  // workspace and side panels are entirely hidden in that stage so the
  // designer sees a focused decision point.
  if (stage === 'chooser') {
    return (
      <CRow>
        <CCol md={12}>
          <CCard className="mb-4">
            <CCardHeader className="d-flex justify-content-between align-items-center">
              <strong>{t('chooser.title')}</strong>
              <LanguageSwitcher />
            </CCardHeader>
            <CCardBody>
              <CRow>
                <CCol md={4}>
                  <CCard className="h-100">
                    <CCardBody className="d-flex flex-column">
                      <CCardTitle>{t('chooser.fromScratch.title')}</CCardTitle>
                      <CCardText className="flex-grow-1">
                        {t('chooser.fromScratch.description')}
                      </CCardText>
                      <CButton color="primary" onClick={startFromScratch}>
                        {t('chooser.fromScratch.cta')}
                      </CButton>
                    </CCardBody>
                  </CCard>
                </CCol>
                <CCol md={4}>
                  <CCard className="h-100">
                    <CCardBody className="d-flex flex-column">
                      <CCardTitle>{t('chooser.template.title')}</CCardTitle>
                      <CCardText className="flex-grow-1">
                        {t('chooser.template.description')}
                      </CCardText>
                      <CButton color="info" onClick={() => setTemplateModalOpen(true)}>
                        {t('chooser.template.cta')}
                      </CButton>
                    </CCardBody>
                  </CCard>
                </CCol>
                <CCol md={4}>
                  <CCard className="h-100">
                    <CCardBody className="d-flex flex-column">
                      <CCardTitle>{t('chooser.extend.title')}</CCardTitle>
                      <CCardText className="flex-grow-1">
                        <Trans
                          i18nKey="chooser.extend.description"
                          ns="editor"
                          components={{ code: <code /> }}
                        />
                      </CCardText>
                      <CButton color="warning" onClick={startFromExtend}>
                        {t('chooser.extend.cta')}
                      </CButton>
                    </CCardBody>
                  </CCard>
                </CCol>
              </CRow>
              <hr />
              <div className="d-flex align-items-center gap-2">
                <CButton
                  color="secondary"
                  variant="outline"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isImporting}
                >
                  {isImporting && <CSpinner size="sm" className="me-2" />}
                  {t('chooser.importJson')}
                </CButton>
                <small className="text-medium-emphasis">
                  {t('chooser.importHint')}
                </small>
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept="application/json,.json"
                style={{ display: 'none' }}
                onChange={(e) => {
                  const file = e.target.files?.[0]
                  e.target.value = ''
                  if (file) handleImportFile(file)
                }}
              />
              {saveError && (
                <CAlert color="danger" className="mt-3">
                  {saveError}
                </CAlert>
              )}
            </CCardBody>
          </CCard>
        </CCol>
        <TemplatePickerModal
          visible={templateModalOpen}
          onClose={() => setTemplateModalOpen(false)}
          onSelect={handleTemplateSelected}
        />
      </CRow>
    )
  }

  return (
    <CRow>
      <EditorTour
        runRequest={tourRunRequest}
        hasHistory={Boolean(strategyId)}
        onFinished={() => setTourRunRequest(null)}
      />
      <CCol md={8}>
        {loadError && (
          <CAlert color="danger" className="mb-3">
            {loadError}
          </CAlert>
        )}
        <CCard className="mb-4">
          <CCardHeader className="d-flex justify-content-between align-items-center">
            <div>
              <strong>{t('header.title')}</strong>
              {strategyId && (
                <small className="text-medium-emphasis ms-2">
                  {t('header.id')}: {strategyId}
                </small>
              )}
              {loadedVersion !== null && (
                <CBadge color="secondary" className="ms-2">
                  {t('header.version', { version: loadedVersion })}
                </CBadge>
              )}
            </div>
            <div className="d-flex align-items-center gap-2">
              <CButton
                color="link"
                size="sm"
                onClick={() => setTourRunRequest('manual')}
              >
                {t('buttons.startTour')}
              </CButton>
              <LanguageSwitcher />
            </div>
          </CCardHeader>
          <CCardBody>
            <CForm className="mb-3">
              <CRow className="mb-2">
                <CCol md={6}>
                  <CFormLabel>{t('form.name')}</CFormLabel>
                  <CFormInput
                    type="text"
                    value={strategyName}
                    onChange={(e) => setStrategyName(e.target.value)}
                    data-tour="editor-name"
                  />
                </CCol>
                <CCol md={6}>
                  <CFormLabel>{t('form.description')}</CFormLabel>
                  <CFormInput
                    type="text"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                  />
                </CCol>
              </CRow>
              {/* Sprint 7: mode selector + parent picker. Changing the
                  mode swaps the toolbox via the useMemo above, which
                  triggers the workspace useEffect to re-inject Blockly.
                  Existing blocks in the workspace stay (Blockly keeps
                  them) but the toolbox flyout changes. */}
              <CRow className="mb-2">
                <CCol md={6} data-tour="editor-mode">
                  <CFormLabel>{t('form.mode')}</CFormLabel>
                  <div>
                    <CFormCheck
                      type="radio"
                      name="mode"
                      id="mode-full"
                      label={t('form.modeFull')}
                      checked={mode === 'DSL_FULL'}
                      onChange={() => setMode('DSL_FULL')}
                      inline
                    />
                    <CFormCheck
                      type="radio"
                      name="mode"
                      id="mode-extend"
                      label={t('form.modeExtend')}
                      checked={mode === 'DSL_EXTEND'}
                      onChange={() => setMode('DSL_EXTEND')}
                      inline
                    />
                  </div>
                </CCol>
                {mode === 'DSL_EXTEND' && (
                  <CCol md={6}>
                    <CFormLabel>{t('form.parent')}</CFormLabel>
                    <CFormSelect value={parentId} onChange={(e) => setParentId(e.target.value)}>
                      <option value="">{t('form.selectParent')}</option>
                      {builtIns.map((b) => (
                        <option key={b.id} value={b.id}>
                          {b.name || b.id}
                        </option>
                      ))}
                    </CFormSelect>
                    {parentLoadError && <small className="text-danger">{parentLoadError}</small>}
                  </CCol>
                )}
              </CRow>
            </CForm>

            <div
              ref={workspaceDivRef}
              data-tour="editor-workspace"
              style={{
                height: '60vh',
                minHeight: 420,
                border: '1px solid #d8dbe0',
                borderRadius: 4,
              }}
            />

            {validationErrors.length > 0 && (
              <CAlert color="warning" className="mt-3">
                <strong>{t('alerts.astErrors')}</strong>
                <ul className="mb-0">
                  {validationErrors.map((err, i) => (
                    <li key={i}>{friendlyValidationMessage(t, err)}</li>
                  ))}
                </ul>
              </CAlert>
            )}
            {saveError && (
              <CAlert color="danger" className="mt-3">
                {saveError}
              </CAlert>
            )}
            {saveSuccess && (
              <CAlert color="success" className="mt-3">
                {saveSuccess}
              </CAlert>
            )}

            <div className="mt-3 d-flex flex-wrap gap-2">
              <CButton
                color="primary"
                onClick={handleSave}
                disabled={isSaving}
                data-tour="editor-save"
              >
                {isSaving ? <CSpinner size="sm" className="me-2" /> : null}
                {t('buttons.save')}
              </CButton>
              <CButton color="info" onClick={handleSimulate} disabled={isSimulating}>
                {isSimulating ? <CSpinner size="sm" className="me-2" /> : null}
                {t('buttons.test')}
              </CButton>
              {/* Sprint 8: import/export bundles. Export is client-side
                  (Blob + <a download>), import POSTs to /import which
                  validates the AST and auto-renames on collision. */}
              <CButton color="secondary" variant="outline" onClick={handleExport}>
                {t('buttons.exportJson')}
              </CButton>
              <CButton
                color="secondary"
                variant="outline"
                onClick={() => fileInputRef.current?.click()}
                disabled={isImporting}
              >
                {isImporting && <CSpinner size="sm" className="me-2" />}
                {t('buttons.importJson')}
              </CButton>
              {/* Sprint 9: only meaningful for already-persisted
                  strategies — for a brand-new draft there's nothing
                  to compare against yet. */}
              {strategyId && (
                <CButton
                  color="secondary"
                  variant="outline"
                  onClick={() => setHistoryOpen(true)}
                  data-tour="editor-history"
                >
                  {t('buttons.history')}
                </CButton>
              )}
              <input
                ref={fileInputRef}
                type="file"
                accept="application/json,.json"
                style={{ display: 'none' }}
                onChange={(e) => {
                  const file = e.target.files?.[0]
                  e.target.value = ''
                  if (file) handleImportFile(file)
                }}
              />
            </div>
          </CCardBody>
        </CCard>

        {/* Sprint 7: read-only side panel describing the parent the
            designer is extending. Surfaces what variables can be
            overridden + the parent's description so designers don't
            have to context-switch to the API docs. */}
        {mode === 'DSL_EXTEND' && parentSchema && (
          <CCard className="mb-4">
            <CCardHeader>
              <strong>
                {t('parentSchema.title', {
                  name: parentSchema.name || parentSchema.id,
                })}
              </strong>
              <CBadge color="info" className="ms-2">
                {t('parentSchema.version', { version: parentSchema.version })}
              </CBadge>
            </CCardHeader>
            <CCardBody>
              {parentSchema.description && (
                <p className="text-medium-emphasis">{parentSchema.description}</p>
              )}
              <h6>{t('parentSchema.variables')}</h6>
              {parentSchema.variables.length === 0 ? (
                <small className="text-medium-emphasis">
                  {t('parentSchema.noVariables')}
                </small>
              ) : (
                <table className="table table-sm table-borderless mb-0">
                  <thead>
                    <tr>
                      <th>{t('parentSchema.name')}</th>
                      <th>{t('parentSchema.type')}</th>
                      <th>{t('parentSchema.defaultValue')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {parentSchema.variables.map((v) => (
                      <tr key={v.name}>
                        <td>
                          <code>{v.name}</code>
                        </td>
                        <td>
                          <CBadge color="secondary">{v.type}</CBadge>
                        </td>
                        <td>
                          <code>
                            {typeof v.currentValue === 'object'
                              ? JSON.stringify(v.currentValue)
                              : String(v.currentValue)}
                          </code>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
              <small className="text-medium-emphasis d-block mt-2">
                {t('parentSchema.hint')}
              </small>
            </CCardBody>
          </CCard>
        )}
      </CCol>

      <CCol md={4}>
        <CCard className="mb-4" data-tour="editor-simulate">
          <CCardHeader>
            <strong>{t('simulate.title')}</strong>
          </CCardHeader>
          <CCardBody>
            <p className="text-medium-emphasis small">{t('simulate.intro')}</p>
            <CForm>
              <div className="mb-2">
                <CFormLabel>{t('simulate.externalUserId')}</CFormLabel>
                <CFormInput
                  type="text"
                  value={simForm.externalUserId}
                  onChange={(e) => setSimForm({ ...simForm, externalUserId: e.target.value })}
                />
              </div>
              <div className="mb-2">
                <CFormLabel>{t('simulate.externalTaskId')}</CFormLabel>
                <CFormInput
                  type="text"
                  value={simForm.externalTaskId}
                  onChange={(e) => setSimForm({ ...simForm, externalTaskId: e.target.value })}
                />
              </div>
              <div className="mb-2">
                <CFormLabel>{t('simulate.externalGameId')}</CFormLabel>
                <CFormInput
                  type="text"
                  value={simForm.externalGameId}
                  onChange={(e) => setSimForm({ ...simForm, externalGameId: e.target.value })}
                />
              </div>
              <div className="mb-2">
                <CFormLabel>{t('simulate.data')}</CFormLabel>
                <CFormTextarea
                  rows={3}
                  value={simForm.dataJson}
                  onChange={(e) => setSimForm({ ...simForm, dataJson: e.target.value })}
                />
                <div className="form-text">{t('simulate.dataHint')}</div>
              </div>
              <div className="mb-2">
                <CFormLabel>{t('simulate.mockState')}</CFormLabel>
                <CFormTextarea
                  rows={5}
                  value={simForm.mockStateJson}
                  onChange={(e) => setSimForm({ ...simForm, mockStateJson: e.target.value })}
                />
                <div className="form-text">
                  <Trans
                    i18nKey="simulate.mockHint"
                    ns="editor"
                    components={{ code: <code /> }}
                  />
                </div>
              </div>
            </CForm>

            {simError && (
              <CAlert color="danger" className="mt-3">
                {simError}
              </CAlert>
            )}

            {simResult && (
              <div className="mt-3">
                <h6>{t('simulate.result')}</h6>
                <CAlert color="success" className="py-2 mb-2">
                  <div>
                    <strong>{t('result.summaryPoints', { points: simResult.points })}</strong>
                  </div>
                  <div className="small">
                    {simResult.caseName
                      ? t('result.ruleApplied', { caseName: simResult.caseName })
                      : t('result.noRuleMatched')}
                  </div>
                </CAlert>
                {simResult.callbackData &&
                  Object.keys(simResult.callbackData).length > 0 && (
                    <div className="small mb-2">
                      <strong>{t('result.callbackData')}:</strong>{' '}
                      <code>{JSON.stringify(simResult.callbackData)}</code>
                    </div>
                  )}
                <h6 className="mt-3">
                  {t('simulate.trace', {
                    count: simResult.executionTrace?.length ?? 0,
                  })}
                </h6>
                {simResult.executionTrace?.length > 0 ? (
                  <ol className="ps-3 mb-2 small" style={{ maxHeight: 220, overflow: 'auto' }}>
                    {simResult.executionTrace.map((entry, i) => (
                      <li key={entry.nodeId ?? i}>
                        {t(`trace.types.${entry.type}`, { defaultValue: entry.type })}
                        {' → '}
                        <code>{JSON.stringify(entry.value)}</code>
                        {entry.branch != null && (
                          <span className="text-medium-emphasis"> ({String(entry.branch)})</span>
                        )}
                      </li>
                    ))}
                  </ol>
                ) : (
                  <p className="small text-medium-emphasis">{t('simulate.noTrace')}</p>
                )}
                <details>
                  <summary className="small text-medium-emphasis" style={{ cursor: 'pointer' }}>
                    {t('result.showTechnical')}
                  </summary>
                  <pre
                    style={{
                      maxHeight: 240,
                      overflow: 'auto',
                      background: '#f5f5f5',
                      padding: 8,
                      borderRadius: 4,
                      fontSize: 12,
                    }}
                  >
                    {JSON.stringify(simResult.executionTrace, null, 2)}
                  </pre>
                </details>
              </div>
            )}
          </CCardBody>
        </CCard>
      </CCol>
      <StrategyVersionHistoryModal
        visible={historyOpen}
        strategyId={strategyId}
        isAdmin={isAdmin}
        onClose={() => setHistoryOpen(false)}
        onRollbackDone={(promoted) => {
          // Server rolled back; navigate the editor onto the newly
          // published version so the workspace reflects the cascade.
          setHistoryOpen(false)
          if (promoted?.id) navigate(`/strategies/editor/${promoted.id}`)
        }}
      />
    </CRow>
  )
}

// Best-effort extractor for axios errors. The endpoints raise FastAPI
// HTTPExceptions whose body is { detail: "..." }; bare network errors get
// the raw message instead.
// Sprint 10: ``t`` is optional so the function still works in non-React
// callers (e.g. tests). When provided, the unknown-error fallback is
// localised; without it we degrade to the Spanish wording.
function extractError(err, t) {
  const detail = err?.response?.data?.detail
  if (typeof detail === 'string' && detail) return detail
  if (detail && typeof detail === 'object' && detail.message) return detail.message
  if (err?.message) return err.message
  return t
    ? t('alerts.unknownError', { defaultValue: 'Error desconocido al contactar el backend.' })
    : 'Error desconocido al contactar el backend.'
}

// Sprint 11: turn a validator error into a localised, actionable
// string. Falls back to the English machine ``message`` when the code
// has no translation (or the error carries no code at all).
function friendlyValidationMessage(t, err) {
  if (err?.code) {
    return t(`validation.${err.code}`, {
      ...(err.params || {}),
      defaultValue: err.message,
    })
  }
  return err?.message || ''
}

// Sprint 11: clear every block warning bubble so a previous failed
// validation doesn't leave stale markers after the designer fixes it.
function clearBlockWarnings(workspace) {
  if (!workspace) return
  for (const block of workspace.getAllBlocks(false)) {
    block.setWarningText(null)
  }
}

// Sprint 11: attach the friendly message as a warning bubble on the
// offending block and focus the first one, so the designer sees WHICH
// block is wrong on the canvas instead of decoding a cryptic node id.
function highlightErrorBlocks(workspace, errors, t) {
  if (!workspace) return
  clearBlockWarnings(workspace)
  let firstBlock = null
  for (const err of errors) {
    if (!err.nodeId) continue
    const block = workspace.getBlockById(err.nodeId)
    if (!block) continue
    block.setWarningText(friendlyValidationMessage(t, err))
    if (!firstBlock) firstBlock = block
  }
  if (firstBlock) {
    firstBlock.select()
    workspace.centerOnBlock(firstBlock.id)
  }
}

// Sprint 8: the ``blocklyXml`` column in StrategyDefinition has carried
// two shapes over time — Blockly's modern JSON state (what handleSave
// writes via ``Blockly.serialization.workspaces.save``) and classic
// Blockly XML (what the hand-authored templates ship). Both are still
// useful so the loader sniffs the leading character instead of forcing
// a migration. Empty / whitespace strings are a no-op so the chooser
// can hand us blank canvases without crashing.
function loadWorkspaceFromSerialized(workspace, serialized) {
  if (!workspace || !serialized) return
  const trimmed = String(serialized).trim()
  if (!trimmed) return
  workspace.clear()
  if (trimmed.startsWith('<')) {
    Blockly.Xml.domToWorkspace(Blockly.utils.xml.textToDom(trimmed), workspace)
  } else {
    Blockly.serialization.workspaces.load(JSON.parse(trimmed), workspace)
  }
}

// Sprint 7: dynamic toolbox flyout for the "Overrides padre" category.
// Blockly calls this callback every time the designer opens the
// category, so a parent change reflects immediately in the next click
// without re-injecting the workspace. Returns an array of DOM elements
// (Blockly's expected shape for category callbacks).
function _buildParentOverrideFlyout(workspace, parentSchema) {
  if (!parentSchema || !Array.isArray(parentSchema.variables)) {
    return []
  }
  const blocks = []
  for (const v of parentSchema.variables) {
    const block = document.createElement('block')
    block.setAttribute('type', 'gd_parent_variable_override')
    // Pre-fill the override block with the variable's name and current
    // default so the designer just edits the value.
    const fieldVar = document.createElement('field')
    fieldVar.setAttribute('name', 'VARIABLE')
    fieldVar.textContent = v.name
    block.appendChild(fieldVar)

    const fieldVal = document.createElement('field')
    fieldVal.setAttribute('name', 'VALUE')
    fieldVal.textContent =
      v.currentValue === null || v.currentValue === undefined
        ? ''
        : typeof v.currentValue === 'object'
          ? JSON.stringify(v.currentValue)
          : String(v.currentValue)
    block.appendChild(fieldVal)

    blocks.push(block)
  }
  // Silence the unused-arg lint without dropping the workspace param —
  // future revisions of this callback may need workspace to build
  // shadow blocks or pre-connected inputs.
  void workspace
  return blocks
}

export default StrategyEditor
