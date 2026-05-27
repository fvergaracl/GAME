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
import * as Blockly from 'blockly'
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
import { DEFAULT_TOOLBOX_XML, EXTEND_TOOLBOX_XML, registerDslBlocks } from './blocks'
import { workspaceToAst } from './dsl/generator'
import { validateAst } from './dsl/validator'
import TemplatePickerModal from './TemplatePickerModal'

// Register the custom block prototypes exactly once per browser tab.
// Calling registerDslBlocks more than once would throw on the second
// Blockly.Blocks.foo assignment; the helper is idempotent for safety.
registerDslBlocks()

const INITIAL_SIM_FORM = {
  externalGameId: 'game-1',
  externalTaskId: 'task-1',
  externalUserId: 'user-1',
  dataJson: '{}',
  mockStateJson: '{\n  "task.measurements_count": 1\n}',
}

const StrategyEditor = () => {
  // Sprint 8: ``/strategies/editor/:id`` reuses the same component to
  // edit an existing strategy. When ``id`` is present we skip the
  // empty-state chooser and jump straight into editing mode after
  // loading the row from the backend.
  const { id: routeStrategyId } = useParams()
  const navigate = useNavigate()

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
    }

    return () => {
      workspace.dispose()
      workspaceRef.current = null
    }
  }, [stage, toolboxXml, pendingTemplate, pendingImportBundle])

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
        if (!cancelled) setLoadError(extractError(err))
      })
    return () => {
      cancelled = true
    }
  }, [routeStrategyId])

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
          setParentLoadError(extractError(err))
          setBuiltIns([])
        }
      })
    return () => {
      cancelled = true
    }
  }, [])

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
        setParentLoadError(extractError(err))
        setParentSchema(null)
        parentSchemaRef.current = null
      })
    return () => {
      cancelled = true
    }
  }, [mode, parentId])

  // ----- Chooser actions (Sprint 8) ----------------------------------------
  const startFromScratch = useCallback(() => {
    setMode('DSL_FULL')
    setParentId('')
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
      setSaveError('Abre el editor antes de exportar.')
      return
    }
    let ast
    try {
      ast = workspaceToAst(workspaceRef.current)
    } catch (err) {
      setSaveError(`No se pudo serializar el workspace: ${err.message}`)
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
        setSaveError(`No se pudo leer el archivo: ${err.message}`)
        return
      }
      if (!bundle || typeof bundle !== 'object' || !bundle.astJson) {
        setSaveError('El archivo no parece un bundle de estrategia: falta astJson.')
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
        setSaveError(extractError(err))
      } finally {
        setIsImporting(false)
      }
    },
    [navigate],
  )

  // ----- Save (create or update) -------------------------------------------
  const buildAndValidateAst = useCallback(() => {
    if (!workspaceRef.current) return null
    const ast = workspaceToAst(workspaceRef.current)
    const result = validateAst(ast)
    if (!result.ok) {
      setValidationErrors(result.errors)
      return null
    }
    setValidationErrors([])
    return ast
  }, [])

  const handleSave = useCallback(async () => {
    setSaveError(null)
    setSaveSuccess(null)
    const ast = buildAndValidateAst()
    if (!ast) return
    if (!strategyName.trim()) {
      setSaveError('El nombre de la estrategia es obligatorio.')
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
      setSaveError('Selecciona una estrategia padre antes de guardar.')
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
        setSaveSuccess(`Estrategia actualizada (v${updated.version}, ${updated.status}).`)
      } else {
        const created = await createCustomStrategy(payload)
        setStrategyId(created.id)
        setSaveSuccess(`Estrategia creada (id ${created.id}, v${created.version}).`)
      }
    } catch (err) {
      setSaveError(extractError(err))
    } finally {
      setIsSaving(false)
    }
  }, [strategyName, description, strategyId, mode, parentId, buildAndValidateAst])

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
      setSimError(`data: JSON inválido (${err.message}).`)
      return
    }
    try {
      mockStateParsed = simForm.mockStateJson ? JSON.parse(simForm.mockStateJson) : {}
    } catch (err) {
      setSimError(`mockState: JSON inválido (${err.message}).`)
      return
    }

    // /simulate requires a persisted strategy id. If the designer hasn't
    // saved yet, persist as a hidden draft first so they can iterate
    // without remembering to click Save before Test.
    let targetId = strategyId
    if (!targetId) {
      try {
        if (mode === 'DSL_EXTEND' && !parentId) {
          setSimError('Selecciona una estrategia padre antes de probar.')
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
        setSimError(extractError(err))
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
      setSimError(extractError(err))
    } finally {
      setIsSimulating(false)
    }
  }, [buildAndValidateAst, simForm, strategyId, strategyName, description, mode, parentId])

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
            <CCardHeader>
              <strong>¿Cómo quieres empezar?</strong>
            </CCardHeader>
            <CCardBody>
              <CRow>
                <CCol md={4}>
                  <CCard className="h-100">
                    <CCardBody className="d-flex flex-column">
                      <CCardTitle>Empezar desde cero</CCardTitle>
                      <CCardText className="flex-grow-1">
                        Workspace en blanco. Útil cuando ya sabes qué reglas quieres modelar.
                      </CCardText>
                      <CButton color="primary" onClick={startFromScratch}>
                        Crear estrategia vacía
                      </CButton>
                    </CCardBody>
                  </CCard>
                </CCol>
                <CCol md={4}>
                  <CCard className="h-100">
                    <CCardBody className="d-flex flex-column">
                      <CCardTitle>Usar una plantilla</CCardTitle>
                      <CCardText className="flex-grow-1">
                        Empieza con un ejemplo listo (engagement, recompensa por completar tarea,
                        bonus de velocidad, ...).
                      </CCardText>
                      <CButton color="info" onClick={() => setTemplateModalOpen(true)}>
                        Elegir plantilla
                      </CButton>
                    </CCardBody>
                  </CCard>
                </CCol>
                <CCol md={4}>
                  <CCard className="h-100">
                    <CCardBody className="d-flex flex-column">
                      <CCardTitle>Extender estrategia existente</CCardTitle>
                      <CCardText className="flex-grow-1">
                        Envuelve una built-in (por ej. <code>default</code>) con reglas pre/post sin
                        reescribirla.
                      </CCardText>
                      <CButton color="warning" onClick={startFromExtend}>
                        Extender existente
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
                  Importar JSON
                </CButton>
                <small className="text-medium-emphasis">
                  Sube un bundle previamente exportado.
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
      <CCol md={8}>
        {loadError && (
          <CAlert color="danger" className="mb-3">
            {loadError}
          </CAlert>
        )}
        <CCard className="mb-4">
          <CCardHeader>
            <strong>Editor de estrategia</strong>
            {strategyId && <small className="text-medium-emphasis ms-2">id: {strategyId}</small>}
            {loadedVersion !== null && (
              <CBadge color="secondary" className="ms-2">
                v{loadedVersion}
              </CBadge>
            )}
          </CCardHeader>
          <CCardBody>
            <CForm className="mb-3">
              <CRow className="mb-2">
                <CCol md={6}>
                  <CFormLabel>Nombre</CFormLabel>
                  <CFormInput
                    type="text"
                    value={strategyName}
                    onChange={(e) => setStrategyName(e.target.value)}
                  />
                </CCol>
                <CCol md={6}>
                  <CFormLabel>Descripción</CFormLabel>
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
                <CCol md={6}>
                  <CFormLabel>Modo</CFormLabel>
                  <div>
                    <CFormCheck
                      type="radio"
                      name="mode"
                      id="mode-full"
                      label="Crear desde cero"
                      checked={mode === 'DSL_FULL'}
                      onChange={() => setMode('DSL_FULL')}
                      inline
                    />
                    <CFormCheck
                      type="radio"
                      name="mode"
                      id="mode-extend"
                      label="Extender existente"
                      checked={mode === 'DSL_EXTEND'}
                      onChange={() => setMode('DSL_EXTEND')}
                      inline
                    />
                  </div>
                </CCol>
                {mode === 'DSL_EXTEND' && (
                  <CCol md={6}>
                    <CFormLabel>Estrategia padre</CFormLabel>
                    <CFormSelect value={parentId} onChange={(e) => setParentId(e.target.value)}>
                      <option value="">— Selecciona padre —</option>
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
              style={{
                height: '60vh',
                minHeight: 420,
                border: '1px solid #d8dbe0',
                borderRadius: 4,
              }}
            />

            {validationErrors.length > 0 && (
              <CAlert color="warning" className="mt-3">
                <strong>El AST tiene errores:</strong>
                <ul className="mb-0">
                  {validationErrors.map((err, i) => (
                    <li key={i}>
                      {err.nodeId ? <code>{err.nodeId}</code> : null} {err.message}
                    </li>
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
              <CButton color="primary" onClick={handleSave} disabled={isSaving}>
                {isSaving ? <CSpinner size="sm" className="me-2" /> : null}
                Guardar borrador
              </CButton>
              <CButton color="info" onClick={handleSimulate} disabled={isSimulating}>
                {isSimulating ? <CSpinner size="sm" className="me-2" /> : null}
                Probar
              </CButton>
              {/* Sprint 8: import/export bundles. Export is client-side
                  (Blob + <a download>), import POSTs to /import which
                  validates the AST and auto-renames on collision. */}
              <CButton color="secondary" variant="outline" onClick={handleExport}>
                Exportar JSON
              </CButton>
              <CButton
                color="secondary"
                variant="outline"
                onClick={() => fileInputRef.current?.click()}
                disabled={isImporting}
              >
                {isImporting && <CSpinner size="sm" className="me-2" />}
                Importar JSON
              </CButton>
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
              <strong>Padre: {parentSchema.name || parentSchema.id}</strong>
              <CBadge color="info" className="ms-2">
                v{parentSchema.version}
              </CBadge>
            </CCardHeader>
            <CCardBody>
              {parentSchema.description && (
                <p className="text-medium-emphasis">{parentSchema.description}</p>
              )}
              <h6>Variables</h6>
              {parentSchema.variables.length === 0 ? (
                <small className="text-medium-emphasis">
                  Esta estrategia no expone variables editables.
                </small>
              ) : (
                <table className="table table-sm table-borderless mb-0">
                  <thead>
                    <tr>
                      <th>Nombre</th>
                      <th>Tipo</th>
                      <th>Valor por defecto</th>
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
                Usa los bloques de la categoría &quot;Overrides padre&quot; para ajustar estos
                valores.
              </small>
            </CCardBody>
          </CCard>
        )}
      </CCol>

      <CCol md={4}>
        <CCard className="mb-4">
          <CCardHeader>
            <strong>Probar estrategia</strong>
          </CCardHeader>
          <CCardBody>
            <CForm>
              <div className="mb-2">
                <CFormLabel>externalGameId</CFormLabel>
                <CFormInput
                  type="text"
                  value={simForm.externalGameId}
                  onChange={(e) => setSimForm({ ...simForm, externalGameId: e.target.value })}
                />
              </div>
              <div className="mb-2">
                <CFormLabel>externalTaskId</CFormLabel>
                <CFormInput
                  type="text"
                  value={simForm.externalTaskId}
                  onChange={(e) => setSimForm({ ...simForm, externalTaskId: e.target.value })}
                />
              </div>
              <div className="mb-2">
                <CFormLabel>externalUserId</CFormLabel>
                <CFormInput
                  type="text"
                  value={simForm.externalUserId}
                  onChange={(e) => setSimForm({ ...simForm, externalUserId: e.target.value })}
                />
              </div>
              <div className="mb-2">
                <CFormLabel>data (JSON)</CFormLabel>
                <CFormTextarea
                  rows={3}
                  value={simForm.dataJson}
                  onChange={(e) => setSimForm({ ...simForm, dataJson: e.target.value })}
                />
              </div>
              <div className="mb-2">
                <CFormLabel>mockState (JSON)</CFormLabel>
                <CFormTextarea
                  rows={5}
                  value={simForm.mockStateJson}
                  onChange={(e) => setSimForm({ ...simForm, mockStateJson: e.target.value })}
                />
                <div className="form-text">
                  Sustituye campos del whitelist por valores fijos, por ejemplo
                  <code> {'{"task.measurements_count": 1}'}</code>.
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
                <h6>Resultado</h6>
                <ul>
                  <li>
                    <strong>points:</strong> {simResult.points}
                  </li>
                  <li>
                    <strong>caseName:</strong> {simResult.caseName ?? '—'}
                  </li>
                  <li>
                    <strong>callbackData:</strong>{' '}
                    <code>{JSON.stringify(simResult.callbackData)}</code>
                  </li>
                </ul>
                <h6 className="mt-3">Trace ({simResult.executionTrace?.length ?? 0} nodos)</h6>
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
              </div>
            )}
          </CCardBody>
        </CCard>
      </CCol>
    </CRow>
  )
}

// Best-effort extractor for axios errors. The endpoints raise FastAPI
// HTTPExceptions whose body is { detail: "..." }; bare network errors get
// the raw message instead.
function extractError(err) {
  return err?.response?.data?.detail || err?.message || 'Error desconocido al contactar el backend.'
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
