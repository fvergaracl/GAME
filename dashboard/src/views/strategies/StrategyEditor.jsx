// Strategy Editor view — embeds a Blockly workspace alongside a "Probar"
// simulate panel (editor 2/3 width, simulate panel 1/3).
//
// State is intentionally simple (no Redux): the workspace is mutated
// imperatively via the Blockly API and held in a ref, so the render tree
// doesn't re-render on every block drag. Save / Simulate read the
// workspace once on click; errors and results go through useState.

import React, { Suspense, useCallback, useEffect, useMemo, useRef, useState } from 'react'
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
  archiveCustomStrategy,
  createCustomStrategy,
  getCustomStrategy,
  getStrategySchema,
  importCustomStrategy,
  listBuiltInStrategies,
  publishCustomStrategy,
  simulateInlineStrategy,
  updateCustomStrategy,
} from '../../api'
import keycloak from '../../keycloak'
import LanguageSwitcher from '../../components/LanguageSwitcher'
import { translateDslError } from '../../i18n/errorMap'
import { extractError } from '../../utils/errors'
import { useToast } from '../../components/Toast'
import {
  STARTER_RULE_XML,
  buildBlockCatalog,
  buildDefaultToolbox,
  buildExtendToolbox,
  refreshBlockI18n,
  registerDslBlocks,
} from './blocks'
import { workspaceToAst } from './dsl/generator'
import { validateAst } from './dsl/validator'
import { buildMockState, usedAccumulationFields } from './dsl/simFields'
import EditorTour from './EditorTour'
import GlossaryHint from './glossary/GlossaryHint'
import { SkeletonCard } from '../../components/Skeleton'

// Lazy-load the heavy on-demand surfaces — none are reachable on first
// paint, and SimulationRunsChart in particular pulls in chart.js.
const SimulationRunsChart = React.lazy(() => import('./SimulationRunsChart'))
const SimulationScenarios = React.lazy(() => import('./SimulationScenarios'))
const SimulationTracePanel = React.lazy(() => import('./SimulationTracePanel'))
const StrategyVersionHistoryModal = React.lazy(() => import('./StrategyVersionHistoryModal'))
const TemplatePickerModal = React.lazy(() => import('./TemplatePickerModal'))

// Feed Blockly's own UI strings (right-click menu, trash confirmations,
// etc.) the user's locale; defaults to Spanish like the rest of the editor.
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
    return decoded?.resource_access?.account?.roles?.includes('AdministratorGAME') || false
  } catch {
    return false
  }
}

// Maps the backend lifecycle status to a CoreUI badge colour. Kept in
// sync with StrategyVersionHistoryModal's STATUS_BADGE.
const STATUS_BADGE = {
  DRAFT: 'secondary',
  PUBLISHED: 'success',
  ARCHIVED: 'dark',
}

const INITIAL_SIM_FORM = {
  externalGameId: 'game-1',
  externalTaskId: 'task-1',
  externalUserId: 'user-1',
  dataJson: '{}',
  mockStateJson: '{}',
}

// Upper bound on cumulative runs so a stray "999" can't hammer the
// backend with sequential simulate calls.
const MAX_CUMULATIVE_RUNS = 50

// Idle delay before autosaving a dirty DRAFT — long enough to fire on a
// real pause, not mid-typing.
const AUTOSAVE_DELAY_MS = 4000

// The "clean" snapshot is the AST plus editable metadata (name /
// description), so a rename also counts as an unsaved change. Stable JSON
// key order makes string comparison reliable.
const composeClean = (ast, name, description) =>
  JSON.stringify({ ast, name: (name || '').trim(), description: (description || '').trim() })

// True when an AST carries something worth persisting — at least one rule
// (main / pre / post) or a default statement. The autosave data-loss guard
// uses it to refuse overwriting a saved-with-content version with an empty
// canvas (F3).
const astHasContent = (ast) =>
  Boolean(
    ast &&
      ((Array.isArray(ast.rules) && ast.rules.length > 0) ||
        (Array.isArray(ast.pre_rules) && ast.pre_rules.length > 0) ||
        (Array.isArray(ast.post_rules) && ast.post_rules.length > 0) ||
        ast.default),
  )

const StrategyEditor = () => {
  const { t, i18n } = useTranslation('editor')
  // Shared feedback channel. No-op outside a ToastProvider (e.g. test
  // harness) so callers don't have to guard.
  const toast = useToast()

  // Sync Blockly's own UI (right-click menus, trash dialog) and re-tooltip
  // every registered block to the active locale. Idempotent by design.
  useEffect(() => {
    applyBlocklyLocale(i18n.resolvedLanguage)
    registerDslBlocks(t)
    if (workspaceRef.current) {
      refreshBlockI18n(workspaceRef.current, t)
    }
  }, [t, i18n.resolvedLanguage])

  // ``/strategies/editor/:id`` reuses this component to edit an existing
  // strategy: when ``id`` is present we skip the chooser and load the row.
  const { id: routeStrategyId } = useParams()
  const navigate = useNavigate()

  // Tour gating: ``auto`` defers to EditorTour's localStorage flag;
  // ``manual`` (from the toolbar) replays the tour on demand.
  const [tourRunRequest, setTourRunRequest] = useState('auto')

  const workspaceDivRef = useRef(null)
  const workspaceRef = useRef(null)
  // The toolbox callback (registered once per workspace) reads the parent
  // schema via this ref, so a parent change needs no workspace re-injection.
  const parentSchemaRef = useRef(null)
  // Debounce timer for recomputing which accumulated fields the strategy
  // reads as the designer edits blocks (see the change listener below).
  const usedFieldsTimerRef = useRef(null)

  const [strategyName, setStrategyName] = useState('Mi estrategia')
  const [description, setDescription] = useState('')
  const [strategyId, setStrategyId] = useState(routeStrategyId || null)
  const [loadedVersion, setLoadedVersion] = useState(null)

  const [mode, setMode] = useState('DSL_FULL')
  const [parentId, setParentId] = useState('')
  const [parentSchema, setParentSchema] = useState(null)
  const [builtIns, setBuiltIns] = useState([])
  const [parentLoadError, setParentLoadError] = useState(null)

  // ``stage`` gates the empty-state chooser: 'chooser' shows the CTAs,
  // 'editing' enters the workspace. Skipped when the route names an id.
  const [stage, setStage] = useState(routeStrategyId ? 'editing' : 'chooser')
  const [templateModalOpen, setTemplateModalOpen] = useState(false)
  const [pendingTemplate, setPendingTemplate] = useState(null)
  const [pendingImportBundle, setPendingImportBundle] = useState(null)
  // Queue a starter rule for the "from scratch" path so the new workspace
  // lands on a valid example instead of a blank canvas that fails validation.
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
  // The exact AST that produced ``simResult`` — kept so the trace panel
  // walks the same tree the interpreter ran (node ids line up 1:1).
  const [simAst, setSimAst] = useState(null)
  // A pinned previous run, shown side-by-side with the current result to
  // compare two tweaks of the same strategy.
  const [comparison, setComparison] = useState(null)

  // Guided "accumulated values" panel. ``simMode`` toggles a single
  // dry-run vs. a cumulative sequence of submissions. ``usedFields`` is
  // the subset of analytics fields the current AST reads, recomputed via
  // a debounced workspace change listener. ``simFieldValues`` holds the
  // per-path { value, step }; ``simRuns`` is the cumulative result table.
  const [simMode, setSimMode] = useState('single')
  const [usedFields, setUsedFields] = useState([])
  const [simFieldValues, setSimFieldValues] = useState({})
  const [cumulativeRuns, setCumulativeRuns] = useState(5)
  const [simRuns, setSimRuns] = useState(null)

  // History modal visibility — only meaningful once ``strategyId`` is set.
  const [historyOpen, setHistoryOpen] = useState(false)
  const isAdmin = useMemo(() => isCurrentUserAdmin(), [])

  // Lifecycle (publish / archive). ``status`` mirrors the backend's
  // DRAFT→PUBLISHED→ARCHIVED state machine to gate which CTA shows;
  // ``lifecycleAction`` drives an inline confirm so a stray click can't
  // publish/archive.
  const [status, setStatus] = useState(null)
  const [lifecycleAction, setLifecycleAction] = useState(null)
  const [isLifecycleBusy, setIsLifecycleBusy] = useState(false)

  // Unsaved-changes tracking + autosave. ``cleanAstRef`` holds the
  // composite (AST + name + description) of the last saved/loaded state;
  // an effect compares the live composite against it to derive ``isDirty``.
  // Comparing the semantic AST (not Blockly coordinates) means a pure
  // reposition isn't a change. ``workspaceRev`` bumps on every block edit
  // so that effect re-runs and resets the autosave debounce.
  const cleanAstRef = useRef(null)
  // F3 (data-loss guards). ``hydratedRef`` stays false until the intended
  // initial content has landed on the canvas, so autosave can't PUT a blank
  // canvas over saved blocks during the load window. ``baselineHasContentRef``
  // mirrors whether the current clean baseline has any rules, so autosave
  // refuses to clobber a with-content version with an empty canvas.
  const hydratedRef = useRef(false)
  const baselineHasContentRef = useRef(false)
  const [isDirty, setIsDirty] = useState(false)
  const [workspaceRev, setWorkspaceRev] = useState(0)
  const [isAutosaving, setIsAutosaving] = useState(false)
  const [autosaveError, setAutosaveError] = useState(null)
  const [lastAutosaveAt, setLastAutosaveAt] = useState(null)

  // The toolbox is rebuilt from ``t()`` so it recomputes on a mode or
  // language change. To avoid re-injecting the workspace on a language
  // switch, the injection effect reads the latest XML via a ref and a
  // separate effect pushes the rebuilt toolbox in-place via
  // ``workspace.updateToolbox`` (which preserves the blocks).
  const toolboxXml = useMemo(
    () => (mode === 'DSL_EXTEND' ? buildExtendToolbox(t) : buildDefaultToolbox(t)),
    [mode, t],
  )
  const toolboxXmlRef = useRef(toolboxXml)
  useEffect(() => {
    toolboxXmlRef.current = toolboxXml
    if (workspaceRef.current) {
      workspaceRef.current.updateToolbox(toolboxXml)
    }
  }, [toolboxXml])

  // Block-search box: the mode + language aware catalog drives the match
  // dropdown; clicking one inserts that block (scanning 20+ blocks by
  // category is slow).
  const [blockSearch, setBlockSearch] = useState('')
  const blockCatalog = useMemo(() => buildBlockCatalog(mode, t), [mode, t])
  const blockSearchResults = useMemo(() => {
    const q = blockSearch.trim().toLowerCase()
    if (!q) return []
    return blockCatalog.filter(
      (b) =>
        b.label.toLowerCase().includes(q) ||
        b.category.toLowerCase().includes(q) ||
        b.type.toLowerCase().includes(q),
    )
  }, [blockSearch, blockCatalog])

  // Insert a searched block at the centre of the current viewport, select
  // it so it's obvious where it landed, then clear the query. Returns
  // silently if the workspace isn't mounted yet.
  const insertBlockFromSearch = useCallback((type) => {
    const workspace = workspaceRef.current
    if (!workspace) return
    const block = Blockly.serialization.blocks.append({ type }, workspace)
    if (block?.id) {
      workspace.centerOnBlock(block.id)
      block.select?.()
    }
    setBlockSearch('')
  }, [])

  // Keep the guided "accumulated values" inputs in sync with the blocks:
  // each edit re-derives which analytics fields the AST reads, so the test
  // panel only shows inputs the strategy uses. Wrapped in try/catch since
  // the AST is often half-built mid-edit. A stable callback (reading the
  // live workspace via ``workspaceRef``) so both the change listener and
  // the hydration effect can call it.
  const refreshUsedFields = useCallback(() => {
    const workspace = workspaceRef.current
    if (!workspace) return
    try {
      const ast = workspaceToAst(workspace)
      const fields = usedAccumulationFields(ast)
      setUsedFields(fields)
      setSimFieldValues((prev) => {
        let changed = false
        const next = { ...prev }
        for (const meta of fields) {
          if (!next[meta.path]) {
            next[meta.path] = { value: meta.default, step: meta.step }
            changed = true
          }
        }
        return changed ? next : prev
      })
    } catch {
      // Malformed AST mid-edit — keep the last known field set.
    }
    // Signal "the workspace changed" so the dirty/autosave effect
    // recomputes. We bump a counter rather than compute dirtiness here
    // because this callback can't see the latest name/description.
    setWorkspaceRev((rev) => rev + 1)
  }, [])

  // ----- Blockly workspace lifecycle ---------------------------------------
  // The workspace only mounts when ``stage === 'editing'``; while the
  // chooser shows, workspaceDivRef.current is null and we skip injection.
  //
  // This effect must inject EXACTLY ONCE per editing session: it depends
  // only on ``stage`` (and the stable ``refreshUsedFields``), NOT on
  // ``mode`` or the ``pending*`` flags. Its body resets those flags, so
  // depending on them would dispose the freshly-hydrated workspace and
  // re-inject an empty one. Mode changes stay in-place via the
  // ``updateToolbox`` effect; content hydration is the effect below.
  useEffect(() => {
    if (stage !== 'editing') return
    if (!workspaceDivRef.current) return
    const workspace = Blockly.inject(workspaceDivRef.current, {
      toolbox: toolboxXmlRef.current,
      trashcan: true,
      scrollbars: true,
      sounds: false,
      // Conservative zoom defaults — designers tend to over-zoom otherwise.
      zoom: { controls: true, wheel: true, startScale: 0.9 },
    })
    workspaceRef.current = workspace

    // The "Overrides padre" category is populated dynamically from the
    // parent schema; registering the callback here lets it read
    // parentSchemaRef.current when the category opens, so a schema change
    // needs no re-injection.
    workspace.registerToolboxCategoryCallback('PARENT_OVERRIDES', (ws) =>
      _buildParentOverrideFlyout(ws, parentSchemaRef.current),
    )

    // Debounced because Blockly fires a change event per drag tick.
    workspace.addChangeListener(() => {
      if (usedFieldsTimerRef.current) clearTimeout(usedFieldsTimerRef.current)
      usedFieldsTimerRef.current = setTimeout(refreshUsedFields, 300)
    })

    return () => {
      if (usedFieldsTimerRef.current) clearTimeout(usedFieldsTimerRef.current)
      workspace.dispose()
      workspaceRef.current = null
    }
  }, [stage, refreshUsedFields])

  // ----- Blockly content hydration -----------------------------------------
  // Split out from injection so loading content never disposes/re-injects
  // the workspace — it operates on the mounted instance via ``workspaceRef``.
  // A queued template / imported bundle / starter seed is applied here;
  // resetting the pending flag afterwards is safe since we don't tear the
  // workspace down. Also runs with no pending content so a fresh empty
  // canvas still captures its clean baseline.
  useEffect(() => {
    const workspace = workspaceRef.current
    if (stage !== 'editing' || !workspace) return

    // Resolve the single queued content source (if any) up front so the
    // try/finally can clear the right flag whether the load succeeds or
    // throws — a corrupt payload must not re-trigger the effect forever.
    let pending = null
    if (pendingTemplate) {
      pending = { xml: pendingTemplate.blocklyXml, clear: () => setPendingTemplate(null) }
    } else if (pendingImportBundle) {
      pending = { xml: pendingImportBundle.blocklyXml, clear: () => setPendingImportBundle(null) }
    } else if (pendingSeed) {
      // Seed a valid starter rule for the from-scratch path.
      pending = { xml: STARTER_RULE_XML, clear: () => setPendingSeed(false) }
    }

    if (pending) {
      try {
        loadWorkspaceFromSerialized(workspace, pending.xml)
      } catch (err) {
        // F4: a corrupt blocklyXml must surface a clear error instead of a
        // silent blank canvas. ``loadWorkspaceFromSerialized`` parses before
        // clearing, so on a parse failure the prior blocks stay put.
        setLoadError(t('alerts.loadFailed', { error: err?.message || String(err) }))
      } finally {
        pending.clear()
      }
    }

    // Reflect any hydrated blocks in the guided inputs immediately (the
    // change listener's debounce may not have fired yet).
    refreshUsedFields()

    // Capture the clean baseline AFTER (attempting to) hydrate so the first
    // real edit flips ``isDirty``. An empty/invalid canvas gets a sentinel so
    // the first dropped block still counts as a change. ``strategyName`` /
    // ``description`` are read here but kept OUT of the deps: the load-by-id
    // effect sets them in the same batch as the pending bundle, and depending
    // on them would re-capture the baseline on every keystroke.
    let baselineAst = null
    try {
      baselineAst = workspaceToAst(workspace)
      cleanAstRef.current = composeClean(baselineAst, strategyName, description)
    } catch {
      cleanAstRef.current = '__EMPTY__'
    }
    setIsDirty(false)

    // F3: track whether the baseline has content (so autosave won't clobber
    // it with an empty canvas) and arm autosave only once the intended
    // content has landed. The initial no-pending pass on the load-by-id path
    // (``routeStrategyId`` set, nothing queued yet) is intentionally left
    // un-hydrated so a blank canvas can never be autosaved over saved blocks
    // before the row arrives; the load-by-id effect handles content-less rows.
    baselineHasContentRef.current = astHasContent(baselineAst)
    if (pending || !routeStrategyId) {
      hydratedRef.current = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- name/description/t/routeStrategyId intentionally excluded (see comment above)
  }, [stage, pendingTemplate, pendingImportBundle, pendingSeed, refreshUsedFields])

  // ----- Load existing strategy by id --------------------------------------
  // When the route carries an id we fetch the row, prime the
  // name/description/mode fields, and queue the saved Blockly state for
  // hydration once the workspace mounts. Runs once per id; later edits
  // stay in-memory until the user navigates away.
  useEffect(() => {
    if (!routeStrategyId) return
    let cancelled = false
    setLoadError(null)
    // F3: a (re)load is in flight — disable autosave until this row's content
    // hydrates so we never PUT a stale/blank canvas over the row being loaded.
    hydratedRef.current = false
    baselineHasContentRef.current = false
    getCustomStrategy(routeStrategyId)
      .then((row) => {
        if (cancelled) return
        setStrategyId(row.id)
        setStrategyName(row.name || '')
        setDescription(row.description || '')
        setLoadedVersion(row.version ?? null)
        setStatus(row.status ?? null)
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
        } else {
          // Nothing to hydrate — the row IS loaded, so it's safe to arm
          // autosave. (The hydration effect only flips ``hydratedRef`` when
          // it has pending content to apply.)
          hydratedRef.current = true
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

  // ----- Chooser actions ---------------------------------------------------
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

  // ----- Import / Export JSON ----------------------------------------------
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

  // Record a "clean" baseline after a successful save/autosave.
  // ``cleanComposite`` is the exact (AST + name + description) persisted —
  // NOT the live workspace — so edits made *during* an in-flight save
  // aren't swallowed. Bumping ``workspaceRev`` re-runs the dirty effect,
  // which stays dirty if the user kept editing while the request was in
  // flight.
  const markClean = useCallback((cleanComposite) => {
    cleanAstRef.current = cleanComposite
    setAutosaveError(null)
    setWorkspaceRev((rev) => rev + 1)
  }, [])

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

    // In DSL_EXTEND the payload carries the parent id; in DSL_FULL
    // parentStrategyId is explicitly null so the backend's
    // _validate_payload rejects any accidental mismatch.
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
        setLoadedVersion(updated.version ?? null)
        setStatus(updated.status ?? null)
        setSaveSuccess(
          t('alerts.saveSuccessUpdate', {
            version: updated.version,
            status: updated.status,
          }),
        )
      } else {
        const created = await createCustomStrategy(payload)
        setStrategyId(created.id)
        setLoadedVersion(created.version ?? null)
        setStatus(created.status ?? 'DRAFT')
        setSaveSuccess(
          t('alerts.saveSuccessCreate', {
            id: created.id,
            version: created.version,
          }),
        )
      }
      // The saved AST + metadata are now the clean baseline.
      markClean(composeClean(ast, strategyName, description))
      baselineHasContentRef.current = astHasContent(ast)
    } catch (err) {
      setSaveError(translateDslError(t, err) || extractError(err, t))
    } finally {
      setIsSaving(false)
    }
  }, [strategyName, description, strategyId, mode, parentId, buildAndValidateAst, markClean, t])

  // ----- Autosave ----------------------------------------------------------
  // Conservative on purpose: only an EXISTING, named DRAFT is autosaved.
  //   * No strategyId  → never auto-create a row; the first persist stays a
  //     deliberate Save/Test (avoids orphan drafts).
  //   * status !== DRAFT → a PUT on a PUBLISHED row forks a new version, so
  //     autosaving published strategies would spam the version history.
  //   * invalid/empty name → skip silently; manual Save surfaces the
  //     validation error instead.
  const doAutosave = useCallback(async () => {
    if (!workspaceRef.current) return
    if (!strategyId || status !== 'DRAFT') return
    if (isSaving || isAutosaving) return
    if (!strategyName.trim()) return
    if (mode === 'DSL_EXTEND' && !parentId) return
    // F3: never autosave before the row's content has hydrated — otherwise
    // the blank canvas shown during the load window could be PUT over the
    // saved blocks (data loss).
    if (!hydratedRef.current) return
    let ast
    try {
      ast = workspaceToAst(workspaceRef.current)
    } catch {
      return
    }
    // F3: refuse to clobber a baseline that has content with an empty canvas —
    // a transient blank/partial canvas (failed hydration, mid-clear) must not
    // wipe saved blocks. A deliberate full delete still persists via Save.
    if (!astHasContent(ast) && baselineHasContentRef.current) return
    if (!validateAst(ast).ok) return
    const blocklyJson = Blockly.serialization.workspaces.save(workspaceRef.current)
    setIsAutosaving(true)
    setAutosaveError(null)
    try {
      const updated = await updateCustomStrategy(strategyId, {
        name: strategyName.trim(),
        description: description.trim() || null,
        type: mode,
        parentStrategyId: mode === 'DSL_EXTEND' ? parentId : null,
        astJson: ast,
        blocklyXml: JSON.stringify(blocklyJson),
      })
      setStrategyId(updated.id)
      setLoadedVersion(updated.version ?? null)
      setStatus(updated.status ?? 'DRAFT')
      markClean(composeClean(ast, strategyName, description))
      baselineHasContentRef.current = astHasContent(ast)
      setLastAutosaveAt(new Date())
    } catch (err) {
      setAutosaveError(translateDslError(t, err) || extractError(err, t))
    } finally {
      setIsAutosaving(false)
    }
  }, [
    strategyId,
    status,
    isSaving,
    isAutosaving,
    strategyName,
    description,
    mode,
    parentId,
    markClean,
    t,
  ])

  // ----- Simulate ----------------------------------------------------------
  // "Probar" POSTs the AST inline, so simulation never writes to the DB and
  // always tests the EXACT blocks on the canvas (unsaved edits included)
  // rather than the last-saved version.
  const handleSimulate = useCallback(async () => {
    setSimError(null)
    setSimResult(null)
    setSimRuns(null)
    setSimAst(null)
    const ast = buildAndValidateAst()
    if (!ast) return

    let dataParsed
    let advancedMock
    try {
      dataParsed = simForm.dataJson ? JSON.parse(simForm.dataJson) : {}
    } catch (err) {
      setSimError(t('alerts.invalidDataJson', { error: err.message }))
      return
    }
    try {
      advancedMock = simForm.mockStateJson ? JSON.parse(simForm.mockStateJson) : {}
    } catch (err) {
      setSimError(t('alerts.invalidMockJson', { error: err.message }))
      return
    }

    // DSL_EXTEND only makes sense against a parent — guard so the designer
    // gets a clear message.
    if (mode === 'DSL_EXTEND' && !parentId) {
      setSimError(t('alerts.noParentSim'))
      return
    }

    const usedPaths = usedFields.map((m) => m.path)
    // Advanced JSON overrides win over the guided inputs, so designers can
    // still force any field (including data.* paths the inputs don't cover).
    const mockForRun = (runIndex) => ({
      ...buildMockState(simFieldValues, usedPaths, runIndex),
      ...advancedMock,
    })

    const runOnce = (runIndex) =>
      simulateInlineStrategy({
        astJson: ast,
        externalGameId: simForm.externalGameId,
        externalTaskId: simForm.externalTaskId,
        externalUserId: simForm.externalUserId,
        data: dataParsed,
        mockState: mockForRun(runIndex),
      })

    setIsSimulating(true)
    try {
      if (simMode === 'cumulative') {
        const total = Math.max(1, Math.min(MAX_CUMULATIVE_RUNS, Number(cumulativeRuns) || 1))
        const runs = []
        let last = null
        for (let i = 0; i < total; i += 1) {
          // Sequential on purpose: keeps the order deterministic and avoids
          // firing N parallel requests at the backend.
          // eslint-disable-next-line no-await-in-loop
          last = await runOnce(i)
          runs.push({
            run: i + 1,
            points: last.points,
            caseName: last.caseName,
          })
        }
        setSimRuns(runs)
        setSimResult(last)
      } else {
        const response = await runOnce(0)
        setSimResult(response)
      }
      setSimAst(ast)
    } catch (err) {
      setSimError(translateDslError(t, err) || extractError(err, t))
    } finally {
      setIsSimulating(false)
    }
  }, [
    buildAndValidateAst,
    simForm,
    simMode,
    simFieldValues,
    usedFields,
    cumulativeRuns,
    mode,
    parentId,
    t,
  ])

  // Snapshot the current result as the comparison baseline; the next run
  // renders beside it so two tweaks can be compared directly.
  const pinComparison = useCallback(() => {
    if (!simResult) return
    setComparison({
      points: simResult.points,
      caseName: simResult.caseName,
      total: simRuns ? simRuns.reduce((sum, r) => sum + (Number(r.points) || 0), 0) : null,
      runs: simRuns ? simRuns.length : null,
    })
  }, [simResult, simRuns])

  // Collect the current test inputs into a serializable scenario (for
  // SimulationScenarios) and apply a loaded one back onto the form.
  const currentScenario = useMemo(
    () => ({
      externalGameId: simForm.externalGameId,
      externalTaskId: simForm.externalTaskId,
      externalUserId: simForm.externalUserId,
      dataJson: simForm.dataJson,
      mockStateJson: simForm.mockStateJson,
      simMode,
      cumulativeRuns,
      simFieldValues,
    }),
    [simForm, simMode, cumulativeRuns, simFieldValues],
  )

  const loadScenario = useCallback((scenario) => {
    if (!scenario) return
    setSimForm({
      externalGameId: scenario.externalGameId ?? INITIAL_SIM_FORM.externalGameId,
      externalTaskId: scenario.externalTaskId ?? INITIAL_SIM_FORM.externalTaskId,
      externalUserId: scenario.externalUserId ?? INITIAL_SIM_FORM.externalUserId,
      dataJson: scenario.dataJson ?? INITIAL_SIM_FORM.dataJson,
      mockStateJson: scenario.mockStateJson ?? INITIAL_SIM_FORM.mockStateJson,
    })
    if (scenario.simMode) setSimMode(scenario.simMode)
    if (scenario.cumulativeRuns != null) setCumulativeRuns(scenario.cumulativeRuns)
    if (scenario.simFieldValues) setSimFieldValues(scenario.simFieldValues)
  }, [])

  // ----- Publish / Archive -------------------------------------------------
  // The lifecycle endpoints are admin-only server-side (``require_admin``);
  // ``isAdmin`` here just hides the CTAs so a non-admin never sees a button
  // that would 403. The confirm step is an inline CAlert in the toolbar.
  const handleLifecycle = useCallback(async () => {
    if (!lifecycleAction || !strategyId) return
    setSaveError(null)
    setSaveSuccess(null)
    setIsLifecycleBusy(true)
    try {
      const updated =
        lifecycleAction === 'publish'
          ? await publishCustomStrategy(strategyId)
          : await archiveCustomStrategy(strategyId)
      if (updated.id) setStrategyId(updated.id)
      if (updated.version != null) setLoadedVersion(updated.version)
      setStatus(updated.status ?? null)
      const msg = t(
        lifecycleAction === 'publish' ? 'alerts.publishSuccess' : 'alerts.archiveSuccess',
        { version: updated.version },
      )
      setSaveSuccess(msg)
      toast.success(msg)
    } catch (err) {
      const msg = translateDslError(t, err) || extractError(err, t)
      setSaveError(msg)
      toast.error(msg)
    } finally {
      setIsLifecycleBusy(false)
      setLifecycleAction(null)
    }
  }, [lifecycleAction, strategyId, t, toast])

  const canPublish = isAdmin && Boolean(strategyId) && status === 'DRAFT'
  const canArchive =
    isAdmin && Boolean(strategyId) && (status === 'DRAFT' || status === 'PUBLISHED')

  // Single source of truth for "unsaved changes" + autosave timing.
  // Re-runs when the blocks (``workspaceRev``), name/description, or
  // ``doAutosave`` change: compares the live composite against the clean
  // baseline to set ``isDirty``, then (when dirty and parseable) arms the
  // debounced autosave. ``doAutosave`` self-gates on DRAFT/strategyId, so
  // non-autosaveable edits still flip the dirty flag without persisting.
  useEffect(() => {
    if (cleanAstRef.current === null) return undefined
    let current = null
    try {
      current = composeClean(workspaceToAst(workspaceRef.current), strategyName, description)
    } catch {
      current = null
    }
    const dirty = current === null || current !== cleanAstRef.current
    setIsDirty(dirty)
    if (!dirty || current === null) return undefined
    const timer = setTimeout(doAutosave, AUTOSAVE_DELAY_MS)
    return () => clearTimeout(timer)
  }, [workspaceRev, strategyName, description, doAutosave])

  // Warn before a full-page unload (tab close / reload) when there's
  // unsaved work. In-app route changes aren't covered — useBlocker needs a
  // data router, which this app's BrowserRouter setup doesn't use.
  useEffect(() => {
    if (!isDirty) return undefined
    const handler = (e) => {
      e.preventDefault()
      e.returnValue = ''
    }
    window.addEventListener('beforeunload', handler)
    return () => window.removeEventListener('beforeunload', handler)
  }, [isDirty])

  // ----- Render ------------------------------------------------------------
  // Render the empty-state chooser as a stand-alone card until we have an
  // id or a user choice; the workspace and side panels are hidden in that
  // stage so the designer sees a focused decision point.
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
                      <CCardTitle>
                        {t('chooser.extend.title')}
                        <GlossaryHint term="dslExtend" />
                      </CCardTitle>
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
                <small className="text-medium-emphasis">{t('chooser.importHint')}</small>
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
        {templateModalOpen && (
          <Suspense fallback={<SkeletonCard lines={4} />}>
            <TemplatePickerModal
              visible={templateModalOpen}
              onClose={() => setTemplateModalOpen(false)}
              onSelect={handleTemplateSelected}
            />
          </Suspense>
        )}
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
              {status && (
                <>
                  <CBadge color={STATUS_BADGE[status] || 'secondary'} className="ms-2">
                    {t(`status.${status}`, { defaultValue: status })}
                  </CBadge>
                  <GlossaryHint
                    term={
                      status === 'PUBLISHED'
                        ? 'published'
                        : status === 'ARCHIVED'
                          ? 'archived'
                          : 'draft'
                    }
                  />
                </>
              )}
              {isDirty && (
                <CBadge color="warning" className="ms-2">
                  {t('header.unsaved')}
                </CBadge>
              )}
            </div>
            <div className="d-flex align-items-center gap-2">
              <CButton color="link" size="sm" onClick={() => setTourRunRequest('manual')}>
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
              {/* Mode selector + parent picker. Changing the mode swaps the
                  toolbox via the useMemo above; the ``updateToolbox`` effect
                  pushes it into the live workspace in place, so the blocks
                  stay and only the flyout changes. */}
              <CRow className="mb-2">
                <CCol md={6} data-tour="editor-mode">
                  <CFormLabel>
                    {t('form.mode')}
                    <GlossaryHint term={mode === 'DSL_EXTEND' ? 'dslExtend' : 'dslFull'} />
                  </CFormLabel>
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
                    <CFormLabel>
                      {t('form.parent')}
                      <GlossaryHint term="parentStrategy" />
                    </CFormLabel>
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

            {/* Block search: with 20+ blocks, scanning the toolbox is slow;
                typing filters by name/category and a click drops the block. */}
            <div className="position-relative mb-2" data-tour="editor-search">
              <CFormInput
                type="search"
                size="sm"
                value={blockSearch}
                placeholder={t('toolbox.search.placeholder')}
                aria-label={t('toolbox.search.ariaLabel')}
                onChange={(e) => setBlockSearch(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && blockSearchResults.length > 0) {
                    e.preventDefault()
                    insertBlockFromSearch(blockSearchResults[0].type)
                  } else if (e.key === 'Escape') {
                    setBlockSearch('')
                  }
                }}
              />
              {blockSearch.trim() && (
                <div
                  className="position-absolute w-100 mt-1 border rounded shadow-sm bg-body"
                  style={{ zIndex: 1050, maxHeight: 260, overflowY: 'auto' }}
                  role="listbox"
                  aria-label={t('toolbox.search.resultsLabel')}
                >
                  {blockSearchResults.length === 0 ? (
                    <div className="px-3 py-2 text-body-secondary small">
                      {t('toolbox.search.noResults', { query: blockSearch.trim() })}
                    </div>
                  ) : (
                    blockSearchResults.map((b) => (
                      <button
                        key={b.type}
                        type="button"
                        role="option"
                        aria-selected="false"
                        className="d-flex justify-content-between align-items-center w-100 px-3 py-2 border-0 bg-transparent text-start"
                        onClick={() => insertBlockFromSearch(b.type)}
                      >
                        <span>{b.label}</span>
                        <small className="text-body-secondary ms-2">
                          {t('toolbox.search.inCategory', { category: b.category })}
                        </small>
                      </button>
                    ))
                  )}
                </div>
              )}
            </div>

            <div
              ref={workspaceDivRef}
              data-tour="editor-workspace"
              style={{
                height: '60vh',
                minHeight: 420,
                border: '1px solid var(--cui-border-color)',
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

            {lifecycleAction && (
              <CAlert color="warning" className="mt-3">
                <strong>
                  {t(
                    lifecycleAction === 'publish'
                      ? 'lifecycle.publishTitle'
                      : 'lifecycle.archiveTitle',
                  )}
                </strong>
                <p className="mb-2">
                  {t(
                    lifecycleAction === 'publish'
                      ? 'lifecycle.publishBody'
                      : 'lifecycle.archiveBody',
                    { version: loadedVersion, name: strategyName },
                  )}
                </p>
                <div className="d-flex gap-2">
                  <CButton
                    color={lifecycleAction === 'publish' ? 'success' : 'dark'}
                    size="sm"
                    onClick={handleLifecycle}
                    disabled={isLifecycleBusy}
                  >
                    {isLifecycleBusy && <CSpinner size="sm" className="me-2" />}
                    {t(
                      lifecycleAction === 'publish'
                        ? 'lifecycle.confirmPublish'
                        : 'lifecycle.confirmArchive',
                    )}
                  </CButton>
                  <CButton
                    color="secondary"
                    size="sm"
                    variant="outline"
                    onClick={() => setLifecycleAction(null)}
                    disabled={isLifecycleBusy}
                  >
                    {t('lifecycle.cancel')}
                  </CButton>
                </div>
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
              {/* Import/export bundles. Export is client-side (Blob + <a
                  download>); import POSTs to /import, which validates the AST
                  and auto-renames on collision. */}
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
              {/* Only meaningful for already-persisted strategies — a
                  brand-new draft has nothing to compare against yet. */}
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
              {/* Admin-only lifecycle controls. Gated by role (UX hint; the
                  server enforces require_admin) and by the backend state
                  machine — Publish only from DRAFT, Archive from DRAFT or
                  PUBLISHED. */}
              {canPublish && (
                <CButton
                  color="success"
                  onClick={() => setLifecycleAction('publish')}
                  disabled={isLifecycleBusy || Boolean(lifecycleAction)}
                >
                  {t('buttons.publish')}
                </CButton>
              )}
              {canArchive && (
                <CButton
                  color="dark"
                  variant="outline"
                  onClick={() => setLifecycleAction('archive')}
                  disabled={isLifecycleBusy || Boolean(lifecycleAction)}
                >
                  {t('buttons.archive')}
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

            {/* Autosave / unsaved-changes status line. */}
            {(isAutosaving || autosaveError || (lastAutosaveAt && !isDirty)) && (
              <div className="mt-2 small">
                {isAutosaving && (
                  <span className="text-medium-emphasis">
                    <CSpinner size="sm" className="me-1" />
                    {t('autosave.saving')}
                  </span>
                )}
                {!isAutosaving && autosaveError && (
                  <span className="text-danger">{t('autosave.error')}</span>
                )}
                {!isAutosaving && !autosaveError && lastAutosaveAt && !isDirty && (
                  <span className="text-medium-emphasis">
                    {t('autosave.savedAt', { time: lastAutosaveAt.toLocaleTimeString() })}
                  </span>
                )}
              </div>
            )}
          </CCardBody>
        </CCard>

        {/* Read-only side panel describing the parent being extended:
            surfaces the overridable variables + description so designers
            don't context-switch to the API docs. */}
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
                <small className="text-medium-emphasis">{t('parentSchema.noVariables')}</small>
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
              <small className="text-medium-emphasis d-block mt-2">{t('parentSchema.hint')}</small>
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
            <Suspense fallback={<SkeletonCard lines={2} />}>
              <SimulationScenarios current={currentScenario} onLoad={loadScenario} />
            </Suspense>
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
                <CFormLabel>
                  {t('simulate.data')}
                  <GlossaryHint term="dataField" />
                </CFormLabel>
                <CFormTextarea
                  rows={3}
                  value={simForm.dataJson}
                  onChange={(e) => setSimForm({ ...simForm, dataJson: e.target.value })}
                />
                <div className="form-text">{t('simulate.dataHint')}</div>
              </div>
              <div className="mb-2">
                <CFormLabel>{t('simulate.mode.label')}</CFormLabel>
                <CFormSelect value={simMode} onChange={(e) => setSimMode(e.target.value)}>
                  <option value="single">{t('simulate.mode.single')}</option>
                  <option value="cumulative">{t('simulate.mode.cumulative')}</option>
                </CFormSelect>
              </div>

              {simMode === 'cumulative' && (
                <div className="mb-2">
                  <CFormLabel>{t('simulate.runs')}</CFormLabel>
                  <CFormInput
                    type="number"
                    min={1}
                    max={MAX_CUMULATIVE_RUNS}
                    value={cumulativeRuns}
                    onChange={(e) => setCumulativeRuns(e.target.value)}
                  />
                  <div className="form-text">{t('simulate.runsHint')}</div>
                </div>
              )}

              <div className="mb-2">
                <CFormLabel className="fw-semibold">{t('simulate.fieldsTitle')}</CFormLabel>
                {usedFields.length === 0 ? (
                  <div className="form-text">{t('simulate.noFields')}</div>
                ) : (
                  <>
                    <div className="form-text mb-2">{t('simulate.fieldsHint')}</div>
                    {usedFields.map((meta) => (
                      <div className="mb-3" key={meta.path}>
                        <CFormLabel className="small mb-1">
                          {t(`simulate.fields.${meta.path}`, { defaultValue: meta.path })}
                        </CFormLabel>
                        <CFormInput
                          type="number"
                          value={simFieldValues[meta.path]?.value ?? meta.default}
                          onChange={(e) =>
                            setSimFieldValues((prev) => ({
                              ...prev,
                              [meta.path]: {
                                value: e.target.value,
                                step: prev[meta.path]?.step ?? meta.step,
                              },
                            }))
                          }
                        />
                        {simMode === 'cumulative' && (
                          <div className="mt-1">
                            <CFormLabel className="small text-medium-emphasis mb-1">
                              {t('simulate.stepLabel')}
                            </CFormLabel>
                            <CFormInput
                              type="number"
                              value={simFieldValues[meta.path]?.step ?? meta.step}
                              onChange={(e) =>
                                setSimFieldValues((prev) => ({
                                  ...prev,
                                  [meta.path]: {
                                    value: prev[meta.path]?.value ?? meta.default,
                                    step: e.target.value,
                                  },
                                }))
                              }
                            />
                          </div>
                        )}
                      </div>
                    ))}
                  </>
                )}
              </div>

              <details className="mb-2">
                <summary className="small text-medium-emphasis" style={{ cursor: 'pointer' }}>
                  {t('simulate.advanced')}
                </summary>
                <div className="mt-2">
                  <CFormLabel>{t('simulate.mockState')}</CFormLabel>
                  <CFormTextarea
                    rows={4}
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
              </details>

              <div className="d-grid mb-2">
                <CButton color="info" onClick={handleSimulate} disabled={isSimulating}>
                  {isSimulating ? <CSpinner size="sm" className="me-2" /> : null}
                  {simMode === 'cumulative'
                    ? t('simulate.runCumulative', {
                        count: Math.max(
                          1,
                          Math.min(MAX_CUMULATIVE_RUNS, Number(cumulativeRuns) || 1),
                        ),
                      })
                    : t('simulate.run')}
                </CButton>
              </div>
            </CForm>

            {simError && (
              <CAlert color="danger" className="mt-3">
                {simError}
              </CAlert>
            )}

            {simRuns && simRuns.length > 0 && (
              <div className="mt-3">
                <h6>{t('simulate.cumulativeResult')}</h6>
                <table className="table table-sm small mb-2">
                  <thead>
                    <tr>
                      <th>{t('simulate.runColumn')}</th>
                      <th>{t('simulate.pointsColumn')}</th>
                      <th>{t('simulate.ruleColumn')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {simRuns.map((r) => (
                      <tr key={r.run}>
                        <td>{r.run}</td>
                        <td>{r.points}</td>
                        <td>{r.caseName || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <div className="small">
                  <strong>
                    {t('simulate.totalPoints', {
                      points: simRuns.reduce((sum, r) => sum + (Number(r.points) || 0), 0),
                    })}
                  </strong>
                </div>
                <Suspense fallback={<SkeletonCard lines={3} />}>
                  <SimulationRunsChart runs={simRuns} />
                </Suspense>
              </div>
            )}

            {simResult && (
              <div className="mt-3">
                <h6>{simRuns ? t('simulate.lastRunDetail') : t('simulate.result')}</h6>
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

                {/* Pin this run to compare it side-by-side with the next,
                    so the effect of a tweak is visible. */}
                <div className="d-flex align-items-center gap-2 mb-2">
                  <CButton size="sm" color="secondary" variant="outline" onClick={pinComparison}>
                    {t('simulate.compare.pin')}
                  </CButton>
                  {comparison && (
                    <CButton
                      size="sm"
                      color="link"
                      className="p-0"
                      onClick={() => setComparison(null)}
                    >
                      {t('simulate.compare.clear')}
                    </CButton>
                  )}
                </div>

                {comparison && (
                  <div className="mb-2">
                    <h6>{t('simulate.compare.title')}</h6>
                    <table className="table table-sm small mb-0">
                      <thead>
                        <tr>
                          <th />
                          <th>{t('simulate.compare.pinned')}</th>
                          <th>{t('simulate.compare.current')}</th>
                          <th>{t('simulate.compare.delta')}</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>{t('simulate.pointsColumn')}</td>
                          <td>{comparison.points}</td>
                          <td>{simResult.points}</td>
                          <td className={deltaClass(simResult.points - comparison.points)}>
                            {formatDelta(simResult.points - comparison.points)}
                          </td>
                        </tr>
                        <tr>
                          <td>{t('simulate.ruleColumn')}</td>
                          <td>{comparison.caseName || '—'}</td>
                          <td>{simResult.caseName || '—'}</td>
                          <td />
                        </tr>
                        {comparison.total != null && simRuns && (
                          <tr>
                            <td>{t('simulate.compare.totalRow')}</td>
                            <td>{comparison.total}</td>
                            <td>{simRuns.reduce((sum, r) => sum + (Number(r.points) || 0), 0)}</td>
                            <td
                              className={deltaClass(
                                simRuns.reduce((sum, r) => sum + (Number(r.points) || 0), 0) -
                                  comparison.total,
                              )}
                            >
                              {formatDelta(
                                simRuns.reduce((sum, r) => sum + (Number(r.points) || 0), 0) -
                                  comparison.total,
                              )}
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                )}
                {simResult.callbackData && Object.keys(simResult.callbackData).length > 0 && (
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
                <div className="mb-2 small" style={{ maxHeight: 340, overflow: 'auto' }}>
                  <Suspense fallback={<SkeletonCard lines={3} />}>
                    <SimulationTracePanel ast={simAst} trace={simResult.executionTrace} />
                  </Suspense>
                </div>
                <details>
                  <summary className="small text-medium-emphasis" style={{ cursor: 'pointer' }}>
                    {t('result.showTechnical')}
                  </summary>
                  <pre
                    className="bg-body-tertiary"
                    style={{
                      maxHeight: 240,
                      overflow: 'auto',
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
      {historyOpen && (
        <Suspense fallback={null}>
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
        </Suspense>
      )}
    </CRow>
  )
}

// Format a points delta with an explicit sign so "+3" / "-2" read at a glance.
function formatDelta(n) {
  const v = Number(n) || 0
  return v > 0 ? `+${v}` : String(v)
}

// Colour the delta: green when the current run scores higher than the
// pinned baseline, red when lower, neutral when equal.
function deltaClass(n) {
  const v = Number(n) || 0
  if (v > 0) return 'text-success'
  if (v < 0) return 'text-danger'
  return 'text-medium-emphasis'
}

// Turn a validator error into a localised, actionable string. Falls back
// to the English machine ``message`` when there's no code/translation.
function friendlyValidationMessage(t, err) {
  if (err?.code) {
    return t(`validation.${err.code}`, {
      ...(err.params || {}),
      defaultValue: err.message,
    })
  }
  return err?.message || ''
}

// Clear every block warning bubble so a previous failed validation doesn't
// leave stale markers after the designer fixes it.
function clearBlockWarnings(workspace) {
  if (!workspace) return
  for (const block of workspace.getAllBlocks(false)) {
    block.setWarningText(null)
  }
}

// Attach the friendly message as a warning bubble on the offending block
// and focus the first one, so the designer sees WHICH block is wrong
// instead of decoding a cryptic node id.
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

// The ``blocklyXml`` column carries two shapes: Blockly's modern JSON
// state (what handleSave writes) and classic Blockly XML (what the
// hand-authored templates ship). The loader sniffs the leading character
// instead of forcing a migration. Empty / whitespace strings are a no-op
// so the chooser can hand us blank canvases without crashing.
function loadWorkspaceFromSerialized(workspace, serialized) {
  if (!workspace || !serialized) return
  const trimmed = String(serialized).trim()
  if (!trimmed) return
  // F4: parse BEFORE clearing so a malformed payload throws while the
  // existing canvas is still intact — a corrupt blocklyXml then leaves the
  // workspace as-is for the caller to flag, instead of silently blanking it.
  if (trimmed.startsWith('<')) {
    const dom = Blockly.utils.xml.textToDom(trimmed)
    workspace.clear()
    Blockly.Xml.domToWorkspace(dom, workspace)
  } else {
    const state = JSON.parse(trimmed)
    workspace.clear()
    Blockly.serialization.workspaces.load(state, workspace)
  }
}

// Dynamic toolbox flyout for the "Overrides padre" category. Blockly calls
// this every time the category opens, so a parent change reflects on the
// next click without re-injecting. Returns an array of DOM elements
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
