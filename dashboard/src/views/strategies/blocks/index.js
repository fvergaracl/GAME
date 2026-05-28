// Sprint 6: custom Blockly block definitions for the strategy DSL.
//
// Each block maps 1:1 to an AST node in app/engine/dsl_ast.py. The
// dropdowns are sourced from the whitelists mirror so they always show
// the same options the backend will accept.
//
// Sprint 10: tooltips and inline labels read from the i18n ``blocks``
// namespace. ``registerDslBlocks`` accepts the i18next ``t`` function so
// the language-switcher can re-register (idempotent) blocks with the
// current locale.

import * as Blockly from 'blockly'

import {
  ARITH_OPS,
  COMPARE_OPS,
  FIELD_PATHS,
  FUNC_NAMES,
} from '../dsl/whitelists'

// Helper: build a [[label, value], ...] options list from a string array.
const optionsFromArray = (arr) => arr.map((v) => [v, v])

// Module-scoped slot for the live ``t`` function. ``registerDslBlocks``
// writes here on first call; subsequent calls update the reference so
// future block ``init()`` invocations (Blockly re-runs init on every
// toolbox open via the prototype) pick up the new locale.
let _t = null

// Sprint 3 (fix C5): per-block documentation route. Used as helpUrl so
// the right-click "Help" opens the real reference doc (the same content
// as docs/dsl/blocks/<slug>.md, bundled via blockDocs.js and rendered by
// BlockHelpView at /strategies/blocks-help/:slug).
//
// helpUrl MUST be a string, never a function: Blockly evaluates a
// function helpUrl on *every* context-menu open (to decide whether the
// Help item is enabled), which would fire a side effect on each right
// click. A plain string is opened with window.open only when clicked.
const HELP_DOC_BASE = '/strategies/blocks-help'
const HELP_SLUGS = {
  gd_rule: 'rule',
  gd_rule_elseif: 'rule',
  gd_rule_else: 'rule',
  gd_compare: 'compare',
  gd_and: 'and',
  gd_or: 'or',
  gd_not: 'not',
  gd_field: 'field',
  gd_field_data: 'field-data',
  gd_literal_number: 'literal-number',
  gd_literal_text: 'literal-text',
  gd_arith: 'arith',
  gd_func_call: 'func-call',
  gd_assign_points: 'assign-points',
  gd_set_callback_data: 'set-callback-data',
  gd_pre_rule: 'pre-rule',
  gd_post_rule: 'post-rule',
  gd_set_data: 'set-data',
  gd_veto: 'veto',
  gd_set_points: 'set-points',
  gd_set_case_name: 'set-case-name',
  gd_field_parent: 'field-parent',
  gd_parent_variable_override: 'parent-variable-override',
}
const HELP_URLS = Object.fromEntries(
  Object.entries(HELP_SLUGS).map(([blockType, slug]) => [blockType, `${HELP_DOC_BASE}/${slug}`]),
)

// Look up a localised label / tooltip with a Spanish fallback so the
// blocks render usable text even before i18next has initialised (e.g.
// during a unit-test snapshot).
const FALLBACK_LABELS = {
  when: 'cuando',
  then: 'entonces',
  elseIf: 'si no, si',
  else: 'si no',
  and: 'y',
  andAlso: 'y también',
  or: 'o',
  orAlso: 'o también',
  not: 'no',
  field: 'campo',
  data: 'data.',
  value: 'valor',
  min: 'min',
  max: 'max',
  assignPoints: 'asignar puntos',
  case: 'caso',
  setCallback: 'guardar dato',
  equals: '=',
  preWhen: 'PRE — cuando',
  postWhen: 'POST — cuando',
  setData: 'set data',
  vetoCase: 'VETO — caso',
  setPoints: 'set puntos',
  setCaseName: 'set caseName',
  parent: 'padre.',
  override: 'override',
}

const label = (key) => {
  if (_t) {
    const out = _t(`blocks:labels.${key}`, { defaultValue: '' })
    if (out) return out
  }
  return FALLBACK_LABELS[key] ?? key
}

const tooltip = (blockKey) => {
  if (_t) {
    const out = _t(`blocks:tooltips.${blockKey}`, { defaultValue: '' })
    if (out) return out
  }
  return ''
}

// ---------------------------------------------------------------------------
// Rule else / else-if mutator
// ---------------------------------------------------------------------------
// Adapted from Blockly's built-in ``controls_if`` mutator. The three rule
// blocks share this single mutator so the generator/validator/interpreter
// see a uniform shape:
//
//   base branch  → WHEN (value) + THEN (statement)   [names unchanged]
//   else-if i    → IF{i} (value) + DO{i} (statement) [i = 1..elseifCount_]
//   else         → ELSE (statement)                  [when hasElse_]
//
// ``saveExtraState`` / ``loadExtraState`` serialise the branch counts so
// Blockly's JSON workspace serialisation round-trips the branches. The
// legacy ``mutationToDom`` / ``domToMutation`` pair is kept so old
// XML-format workspaces (templates) still load.
const RULE_MUTATOR_MIXIN = {
  elseifCount_: 0,
  elseCount_: 0,

  mutationToDom() {
    if (!this.elseifCount_ && !this.elseCount_) return null
    const container = Blockly.utils.xml.createElement('mutation')
    if (this.elseifCount_) {
      container.setAttribute('elseif', String(this.elseifCount_))
    }
    if (this.elseCount_) container.setAttribute('else', '1')
    return container
  },

  domToMutation(xmlElement) {
    this.elseifCount_ = parseInt(xmlElement.getAttribute('elseif'), 10) || 0
    this.elseCount_ = parseInt(xmlElement.getAttribute('else'), 10) || 0
    this.rebuildShape_()
  },

  saveExtraState() {
    if (!this.elseifCount_ && !this.elseCount_) return null
    const state = Object.create(null)
    if (this.elseifCount_) state.elseIfCount = this.elseifCount_
    if (this.elseCount_) state.hasElse = true
    return state
  },

  loadExtraState(state) {
    this.elseifCount_ = state.elseIfCount || 0
    this.elseCount_ = state.hasElse ? 1 : 0
    this.updateShape_()
  },

  decompose(workspace) {
    const containerBlock = workspace.newBlock('gd_rule_if')
    containerBlock.initSvg()
    let connection = containerBlock.nextConnection
    for (let i = 1; i <= this.elseifCount_; i++) {
      const elseifBlock = workspace.newBlock('gd_rule_elseif')
      elseifBlock.initSvg()
      connection.connect(elseifBlock.previousConnection)
      connection = elseifBlock.nextConnection
    }
    if (this.elseCount_) {
      const elseBlock = workspace.newBlock('gd_rule_else')
      elseBlock.initSvg()
      connection.connect(elseBlock.previousConnection)
    }
    return containerBlock
  },

  compose(containerBlock) {
    let clauseBlock = containerBlock.nextConnection.targetBlock()
    this.elseifCount_ = 0
    this.elseCount_ = 0
    const valueConnections = [null]
    const statementConnections = [null]
    let elseStatementConnection = null
    while (clauseBlock) {
      if (!clauseBlock.isInsertionMarker()) {
        switch (clauseBlock.type) {
          case 'gd_rule_elseif':
            this.elseifCount_++
            valueConnections.push(clauseBlock.valueConnection_)
            statementConnections.push(clauseBlock.statementConnection_)
            break
          case 'gd_rule_else':
            this.elseCount_++
            elseStatementConnection = clauseBlock.statementConnection_
            break
          default:
            throw new TypeError('Unknown block type: ' + clauseBlock.type)
        }
      }
      clauseBlock = clauseBlock.getNextBlock()
    }
    this.updateShape_()
    this.reconnectChildBlocks_(
      valueConnections, statementConnections, elseStatementConnection,
    )
  },

  saveConnections(containerBlock) {
    let clauseBlock = containerBlock.nextConnection.targetBlock()
    let i = 1
    while (clauseBlock) {
      if (!clauseBlock.isInsertionMarker()) {
        switch (clauseBlock.type) {
          case 'gd_rule_elseif': {
            const inputIf = this.getInput('IF' + i)
            const inputDo = this.getInput('DO' + i)
            clauseBlock.valueConnection_ =
              inputIf && inputIf.connection.targetConnection
            clauseBlock.statementConnection_ =
              inputDo && inputDo.connection.targetConnection
            i++
            break
          }
          case 'gd_rule_else': {
            const inputElse = this.getInput('ELSE')
            clauseBlock.statementConnection_ =
              inputElse && inputElse.connection.targetConnection
            break
          }
          default:
            throw new TypeError('Unknown block type: ' + clauseBlock.type)
        }
      }
      clauseBlock = clauseBlock.getNextBlock()
    }
  },

  rebuildShape_() {
    const valueConnections = [null]
    const statementConnections = [null]
    let elseStatementConnection = null
    if (this.getInput('ELSE')) {
      elseStatementConnection = this.getInput('ELSE').connection.targetConnection
    }
    for (let i = 1; this.getInput('IF' + i); i++) {
      const inputIf = this.getInput('IF' + i)
      const inputDo = this.getInput('DO' + i)
      valueConnections.push(inputIf.connection.targetConnection)
      statementConnections.push(inputDo.connection.targetConnection)
    }
    this.updateShape_()
    this.reconnectChildBlocks_(
      valueConnections, statementConnections, elseStatementConnection,
    )
  },

  updateShape_() {
    if (this.getInput('ELSE')) this.removeInput('ELSE')
    for (let i = 1; this.getInput('IF' + i); i++) {
      this.removeInput('IF' + i)
      this.removeInput('DO' + i)
    }
    for (let i = 1; i <= this.elseifCount_; i++) {
      this.appendValueInput('IF' + i)
        .setCheck(['Boolean', 'Number'])
        .appendField(label('elseIf'))
      this.appendStatementInput('DO' + i)
        .setCheck('Statement')
        .appendField(label('then'))
    }
    if (this.elseCount_) {
      this.appendStatementInput('ELSE')
        .setCheck('Statement')
        .appendField(label('else'))
    }
  },

  reconnectChildBlocks_(
    valueConnections, statementConnections, elseStatementConnection,
  ) {
    for (let i = 1; i <= this.elseifCount_; i++) {
      if (valueConnections[i]) valueConnections[i].reconnect(this, 'IF' + i)
      if (statementConnections[i]) {
        statementConnections[i].reconnect(this, 'DO' + i)
      }
    }
    if (elseStatementConnection) {
      elseStatementConnection.reconnect(this, 'ELSE')
    }
  },
}

/**
 * Register the rule mutator extension plus its three popup sub-blocks
 * (container + draggable else-if / else clauses). Idempotent: guarded so a
 * dev-server hot reload doesn't throw on a duplicate registration.
 */
function registerRuleMutator(Blockly) {
  // Sub-blocks shown inside the mutator popup. ``gd_rule_if`` is the
  // immovable container (the base when/then branch); the other two are
  // draggable into the stack to add clauses.
  Blockly.Blocks.gd_rule_if = {
    init() {
      this.appendDummyInput().appendField(label('when'))
      this.setNextStatement(true)
      this.setColour(210)
      this.setTooltip(tooltip('gd_rule_if'))
      this.contextMenu = false
    },
  }
  Blockly.Blocks.gd_rule_elseif = {
    init() {
      this.appendDummyInput().appendField(label('elseIf'))
      this.setPreviousStatement(true)
      this.setNextStatement(true)
      this.setColour(210)
      this.setTooltip(tooltip('gd_rule_elseif'))
      this.contextMenu = false
    },
  }
  Blockly.Blocks.gd_rule_else = {
    init() {
      this.appendDummyInput().appendField(label('else'))
      this.setPreviousStatement(true)
      this.setNextStatement(true)
      this.setColour(210)
      this.setTooltip(tooltip('gd_rule_else'))
      this.contextMenu = false
    },
  }

  if (!Blockly.Extensions.isRegistered('gd_rule_mutator')) {
    Blockly.Extensions.registerMutator(
      'gd_rule_mutator',
      RULE_MUTATOR_MIXIN,
      null,
      ['gd_rule_elseif', 'gd_rule_else'],
    )
  }
}

/**
 * Define a rule-shaped block (base WHEN/THEN branch + else / else-if
 * mutator). Shared by gd_rule, gd_pre_rule and gd_post_rule which differ
 * only in their ``when`` label, colour, tooltip and help URL.
 */
function defineRuleBlock(Blockly, name, { whenLabel, colour, tooltipKey, helpUrl }) {
  Blockly.Blocks[name] = {
    init() {
      // ``WHEN`` accepts Boolean OR Number so a bare ``literal true`` or
      // a numeric field (used as truthy) can be plugged directly without
      // a compare wrapper, mirroring the backend interpreter at
      // app/engine/dsl_interpreter.py ("Allow bare expressions as
      // conditions").
      this.appendValueInput('WHEN')
        .setCheck(['Boolean', 'Number'])
        .appendField(label(whenLabel))
      this.appendStatementInput('THEN')
        .setCheck('Statement')
        .appendField(label('then'))
      this.setColour(colour)
      this.setTooltip(tooltip(tooltipKey))
      this.setHelpUrl(helpUrl)
      Blockly.Extensions.apply('gd_rule_mutator', this, true)
    },
  }
}

let _registered = false

/**
 * Register all DSL blocks with the Blockly registry. Idempotent — calling
 * this twice is a no-op for the registry but DOES update the cached
 * ``t`` reference so future Blockly ``init`` calls reflect the new
 * locale (used by the language switcher).
 */
export function registerDslBlocks(tFn) {
  if (tFn) _t = tFn
  if (_registered) return
  _registered = true

  // ---- rule mutator ------------------------------------------------------
  // ``gd_rule`` / ``gd_pre_rule`` / ``gd_post_rule`` all share the same
  // ``cuando``/``entonces`` shape AND the same else / else-if mutator, so
  // the branching logic lives once here and is applied to each block via
  // ``defineRuleBlock``. The mixin is adapted from Blockly's built-in
  // ``controls_if`` mutator: the base branch keeps the existing WHEN/THEN
  // input names (so previously-saved workspaces still load), and extra
  // branches use IF{n}/DO{n} (n>=1) plus a single ELSE statement input —
  // exactly the names controls_if uses for its dynamic clauses.
  registerRuleMutator(Blockly)

  // ---- gd_rule -----------------------------------------------------------
  // Statement-shaped root that holds one ``when`` condition, a stack of
  // ``then`` statements, and optional else-if / else branches added via the
  // mutator. Top-level on the workspace; not connectable to anything else.
  defineRuleBlock(Blockly, 'gd_rule', {
    whenLabel: 'when',
    colour: 210,
    tooltipKey: 'gd_rule',
    helpUrl: HELP_URLS.gd_rule,
  })

  // ---- gd_compare --------------------------------------------------------
  Blockly.Blocks.gd_compare = {
    init() {
      this.appendValueInput('LEFT').setCheck(['Number', 'String'])
      this.appendDummyInput()
        .appendField(new Blockly.FieldDropdown(optionsFromArray(COMPARE_OPS)), 'OP')
      this.appendValueInput('RIGHT').setCheck(['Number', 'String'])
      this.setInputsInline(true)
      this.setOutput(true, 'Boolean')
      this.setColour(180)
      this.setTooltip(tooltip('gd_compare'))
      this.setHelpUrl(HELP_URLS.gd_compare)
    },
  }

  // ---- gd_and / gd_or (binary for MVP — mutator for variadic in S7) ------
  Blockly.Blocks.gd_and = {
    init() {
      this.appendValueInput('A').setCheck('Boolean').appendField(label('and'))
      this.appendValueInput('B').setCheck('Boolean').appendField(label('andAlso'))
      this.setOutput(true, 'Boolean')
      this.setInputsInline(true)
      this.setColour(150)
      this.setTooltip(tooltip('gd_and'))
      this.setHelpUrl(HELP_URLS.gd_and)
    },
  }
  Blockly.Blocks.gd_or = {
    init() {
      this.appendValueInput('A').setCheck('Boolean').appendField(label('or'))
      this.appendValueInput('B').setCheck('Boolean').appendField(label('orAlso'))
      this.setOutput(true, 'Boolean')
      this.setInputsInline(true)
      this.setColour(150)
      this.setTooltip(tooltip('gd_or'))
      this.setHelpUrl(HELP_URLS.gd_or)
    },
  }

  // ---- gd_not ------------------------------------------------------------
  Blockly.Blocks.gd_not = {
    init() {
      this.appendValueInput('ARG').setCheck('Boolean').appendField(label('not'))
      this.setOutput(true, 'Boolean')
      this.setColour(150)
      this.setTooltip(tooltip('gd_not'))
      this.setHelpUrl(HELP_URLS.gd_not)
    },
  }

  // ---- gd_field ----------------------------------------------------------
  // Picks a whitelisted analytic path. ``data.<key>`` is handled by the
  // separate gd_field_data block so the dropdown doesn't drown the
  // designer in arbitrary keys.
  Blockly.Blocks.gd_field = {
    init() {
      this.appendDummyInput()
        .appendField(label('field'))
        .appendField(
          new Blockly.FieldDropdown(optionsFromArray(FIELD_PATHS)),
          'PATH',
        )
      this.setOutput(true, 'Number')
      this.setColour(290)
      this.setTooltip(tooltip('gd_field'))
      this.setHelpUrl(HELP_URLS.gd_field)
    },
  }

  // ---- gd_field_data -----------------------------------------------------
  // Dynamic ``data.<key>`` reader for caller-supplied event payload.
  Blockly.Blocks.gd_field_data = {
    init() {
      this.appendDummyInput()
        .appendField(label('data'))
        .appendField(
          new Blockly.FieldTextInput('my_key', (value) => {
            // Mirror the backend regex: [A-Za-z0-9_]+
            return /^[A-Za-z0-9_]+$/.test(value) ? value : null
          }),
          'KEY',
        )
      this.setOutput(true, ['Number', 'String', 'Boolean'])
      this.setColour(290)
      this.setTooltip(tooltip('gd_field_data'))
      this.setHelpUrl(HELP_URLS.gd_field_data)
    },
  }

  // ---- gd_literal_number / gd_literal_text -------------------------------
  Blockly.Blocks.gd_literal_number = {
    init() {
      this.appendDummyInput()
        .appendField(new Blockly.FieldNumber(0), 'VALUE')
      this.setOutput(true, 'Number')
      this.setColour(330)
      this.setTooltip(tooltip('gd_literal_number'))
      this.setHelpUrl(HELP_URLS.gd_literal_number)
    },
  }
  Blockly.Blocks.gd_literal_text = {
    init() {
      this.appendDummyInput()
        .appendField('"')
        .appendField(new Blockly.FieldTextInput(''), 'VALUE')
        .appendField('"')
      this.setOutput(true, 'String')
      this.setColour(330)
      this.setTooltip(tooltip('gd_literal_text'))
      this.setHelpUrl(HELP_URLS.gd_literal_text)
    },
  }

  // ---- gd_arith ----------------------------------------------------------
  Blockly.Blocks.gd_arith = {
    init() {
      this.appendValueInput('LEFT').setCheck('Number')
      this.appendDummyInput()
        .appendField(new Blockly.FieldDropdown(optionsFromArray(ARITH_OPS)), 'OP')
      this.appendValueInput('RIGHT').setCheck('Number')
      this.setInputsInline(true)
      this.setOutput(true, 'Number')
      this.setColour(230)
      this.setTooltip(tooltip('gd_arith'))
      this.setHelpUrl(HELP_URLS.gd_arith)
    },
  }

  // ---- gd_func_call ------------------------------------------------------
  // Arity adapts to the selected function via a simple onchange handler.
  // ``int`` exposes one arg (VALUE); ``clamp`` exposes three (VALUE, LO, HI).
  Blockly.Blocks.gd_func_call = {
    init() {
      this.appendDummyInput('HEADER')
        .appendField(
          new Blockly.FieldDropdown(
            optionsFromArray(FUNC_NAMES),
            (newName) => {
              // Re-build args slots whenever the function name changes.
              // Blockly invokes the validator first; we defer the
              // structural rebuild to the next tick so the field value
              // is committed when _rebuildArgs reads it.
              setTimeout(() => this._rebuildArgs(newName), 0)
              return newName
            },
          ),
          'NAME',
        )
      this.setOutput(true, 'Number')
      this.setColour(230)
      this.setTooltip(tooltip('gd_func_call'))
      this.setHelpUrl(HELP_URLS.gd_func_call)
      this._rebuildArgs('int')
    },
    _rebuildArgs(name) {
      // Tear down any existing arg slots.
      for (const inputName of ['VALUE', 'LO', 'HI']) {
        if (this.getInput(inputName)) this.removeInput(inputName)
      }
      if (name === 'int') {
        this.appendValueInput('VALUE').setCheck('Number').appendField(label('value'))
      } else if (name === 'clamp') {
        this.appendValueInput('VALUE').setCheck('Number').appendField(label('value'))
        this.appendValueInput('LO').setCheck('Number').appendField(label('min'))
        this.appendValueInput('HI').setCheck('Number').appendField(label('max'))
      }
      this.setInputsInline(true)
    },
  }

  // ---- gd_assign_points --------------------------------------------------
  // Terminator: no nextStatement. Mirrors the interpreter's halt-on-first-
  // ``assign_points`` semantics — once you assign, the rule is done.
  Blockly.Blocks.gd_assign_points = {
    init() {
      this.appendValueInput('VALUE')
        .setCheck('Number')
        .appendField(label('assignPoints'))
      this.appendDummyInput()
        .appendField(label('case'))
        .appendField(new Blockly.FieldTextInput('default'), 'CASE_NAME')
      this.setPreviousStatement(true, 'Statement')
      // No nextStatement: assign_points halts the rule.
      this.setColour(60)
      this.setTooltip(tooltip('gd_assign_points'))
      this.setHelpUrl(HELP_URLS.gd_assign_points)
    },
  }

  // ---- gd_set_callback_data ----------------------------------------------
  Blockly.Blocks.gd_set_callback_data = {
    init() {
      this.appendDummyInput()
        .appendField(label('setCallback'))
        .appendField(new Blockly.FieldTextInput('clave'), 'KEY')
      this.appendValueInput('VALUE')
        .setCheck(['Number', 'String', 'Boolean'])
        .appendField(label('equals'))
      this.setInputsInline(true)
      this.setPreviousStatement(true, 'Statement')
      this.setNextStatement(true, 'Statement')
      this.setColour(0)
      this.setTooltip(tooltip('gd_set_callback_data'))
      this.setHelpUrl(HELP_URLS.gd_set_callback_data)
    },
  }

  // ========================================================================
  // Sprint 7: DSL_EXTEND blocks. These only appear in the toolbox when
  // the editor is in "Extender existente" mode. The generator routes
  // top-level gd_pre_rule / gd_post_rule into program.pre_rules /
  // post_rules respectively, and top-level gd_parent_variable_override
  // into program.parent_variables.
  // ========================================================================

  // ---- gd_pre_rule -------------------------------------------------------
  // Same shape (and else / else-if mutator) as gd_rule but emits into
  // pre_rules[]. Visually distinguished by colour so the designer sees at
  // a glance which section a rule belongs to.
  defineRuleBlock(Blockly, 'gd_pre_rule', {
    whenLabel: 'preWhen',
    colour: 330,
    tooltipKey: 'gd_pre_rule',
    helpUrl: HELP_URLS.gd_pre_rule,
  })

  // ---- gd_post_rule ------------------------------------------------------
  defineRuleBlock(Blockly, 'gd_post_rule', {
    whenLabel: 'postWhen',
    colour: 60,
    tooltipKey: 'gd_post_rule',
    helpUrl: HELP_URLS.gd_post_rule,
  })

  // ---- gd_set_data -------------------------------------------------------
  // Mutates the working_data dict the parent built-in will receive. Key
  // must be alphanumeric+underscore so it's addressable via data.<key>.
  Blockly.Blocks.gd_set_data = {
    init() {
      this.appendDummyInput()
        .appendField(label('setData'))
        .appendField(new Blockly.FieldTextInput('mi_clave'), 'KEY')
      this.appendValueInput('VALUE')
        .setCheck(['Number', 'String', 'Boolean'])
        .appendField(label('equals'))
      this.setInputsInline(true)
      this.setPreviousStatement(true, 'Statement')
      this.setNextStatement(true, 'Statement')
      this.setColour(330)
      this.setTooltip(tooltip('gd_set_data'))
      this.setHelpUrl(HELP_URLS.gd_set_data)
    },
  }

  // ---- gd_veto -----------------------------------------------------------
  // Terminator: when this fires, the parent and post_rules never run.
  // The final result is (0, case_name).
  Blockly.Blocks.gd_veto = {
    init() {
      this.appendDummyInput()
        .appendField(label('vetoCase'))
        .appendField(new Blockly.FieldTextInput('TooEarly'), 'CASE_NAME')
      this.setPreviousStatement(true, 'Statement')
      // No nextStatement: veto halts the entire pipeline.
      this.setColour(0)
      this.setTooltip(tooltip('gd_veto'))
      this.setHelpUrl(HELP_URLS.gd_veto)
    },
  }

  // ---- gd_set_points -----------------------------------------------------
  // Post-rule override. Unlike assign_points (which halts), set_points
  // lets the rest of the post-rule keep running so a designer can chain
  // set_points + set_callback_data inside one rule.
  Blockly.Blocks.gd_set_points = {
    init() {
      this.appendValueInput('VALUE')
        .setCheck('Number')
        .appendField(label('setPoints'))
      this.setPreviousStatement(true, 'Statement')
      this.setNextStatement(true, 'Statement')
      this.setColour(60)
      this.setTooltip(tooltip('gd_set_points'))
      this.setHelpUrl(HELP_URLS.gd_set_points)
    },
  }

  // ---- gd_set_case_name --------------------------------------------------
  Blockly.Blocks.gd_set_case_name = {
    init() {
      this.appendValueInput('VALUE')
        .setCheck('String')
        .appendField(label('setCaseName'))
      this.setPreviousStatement(true, 'Statement')
      this.setNextStatement(true, 'Statement')
      this.setColour(60)
      this.setTooltip(tooltip('gd_set_case_name'))
      this.setHelpUrl(HELP_URLS.gd_set_case_name)
    },
  }

  // ---- gd_field_parent ---------------------------------------------------
  // Reads parent.points or parent.case_name. Only valid in post_rules —
  // the client-side validator catches mis-placement.
  Blockly.Blocks.gd_field_parent = {
    init() {
      this.appendDummyInput()
        .appendField(label('parent'))
        .appendField(
          new Blockly.FieldDropdown([
            ['points', 'parent.points'],
            ['case_name', 'parent.case_name'],
          ]),
          'PATH',
        )
      // Output type allows both Number and String so it can plug into
      // arith blocks (points → Number) or compare-with-string (case
      // name → String).
      this.setOutput(true, ['Number', 'String'])
      this.setColour(290)
      this.setTooltip(tooltip('gd_field_parent'))
      this.setHelpUrl(HELP_URLS.gd_field_parent)
    },
  }

  // ---- gd_parent_variable_override --------------------------------------
  // Top-level block that emits an entry into program.parent_variables.
  // The VARIABLE dropdown is intentionally a single editable text field
  // here — the dynamic flyout in StrategyEditor.jsx pre-fills the
  // correct value and variable name from the parent's schema, so the
  // designer never has to type a variable name by hand in normal use.
  Blockly.Blocks.gd_parent_variable_override = {
    init() {
      this.appendDummyInput()
        .appendField(label('override'))
        .appendField(
          new Blockly.FieldTextInput('variable_basic_points'),
          'VARIABLE',
        )
        .appendField(label('equals'))
        .appendField(new Blockly.FieldTextInput('1'), 'VALUE')
      this.setColour(20)
      this.setTooltip(tooltip('gd_parent_variable_override'))
      this.setHelpUrl(HELP_URLS.gd_parent_variable_override)
    },
  }
}

/**
 * Default toolbox XML — groups the Sprint 6 blocks into 6 designer-facing
 * categories. Used in "Crear desde cero" (DSL_FULL) mode.
 */
export const DEFAULT_TOOLBOX_XML = `
<xml xmlns="https://developers.google.com/blockly/xml">
  <category name="Cuándo" colour="210">
    <block type="gd_rule"></block>
  </category>
  <category name="Compara" colour="180">
    <block type="gd_compare"></block>
    <block type="gd_and"></block>
    <block type="gd_or"></block>
    <block type="gd_not"></block>
  </category>
  <category name="Campos" colour="290">
    <block type="gd_field"></block>
    <block type="gd_field_data"></block>
  </category>
  <category name="Calcula" colour="230">
    <block type="gd_arith"></block>
    <block type="gd_func_call"></block>
  </category>
  <category name="Valores" colour="330">
    <block type="gd_literal_number"></block>
    <block type="gd_literal_text"></block>
  </category>
  <category name="Asigna" colour="60">
    <block type="gd_assign_points"></block>
    <block type="gd_set_callback_data"></block>
  </category>
</xml>
`.trim()


/**
 * Sprint 11: starter rule seeded into a brand-new DSL_FULL workspace
 * ("Crear estrategia vacía"). A blank canvas made every first
 * Save/Test fail with "rule.then must be a non-empty array of
 * statements" because the designer hadn't connected an action yet.
 * Seeding a working example (when user.measurements_count <= 2 →
 * assign 1 point) gives them a valid, editable skeleton from frame one.
 *
 * Structure is copied from the vetted engagement_basico.json template
 * (all field paths are whitelisted). Block ``id`` attributes are
 * intentionally omitted so Blockly mints fresh ones — avoids any id
 * collision and matches a genuinely new rule.
 */
export const STARTER_RULE_XML = `
<xml xmlns="https://developers.google.com/blockly/xml">
  <block type="gd_rule" x="40" y="40">
    <value name="WHEN">
      <block type="gd_compare">
        <field name="OP">&lt;=</field>
        <value name="LEFT">
          <block type="gd_field">
            <field name="PATH">user.measurements_count</field>
          </block>
        </value>
        <value name="RIGHT">
          <block type="gd_literal_number">
            <field name="VALUE">2</field>
          </block>
        </value>
      </block>
    </value>
    <statement name="THEN">
      <block type="gd_assign_points">
        <value name="VALUE">
          <block type="gd_literal_number">
            <field name="VALUE">1</field>
          </block>
        </value>
        <field name="CASE_NAME">default</field>
      </block>
    </statement>
  </block>
</xml>
`.trim()


/**
 * Sprint 7: extended toolbox XML used in "Extender existente"
 * (DSL_EXTEND) mode. Adds three categories sourced from the Sprint 7
 * blocks plus a callback-backed "Parent overrides" category whose
 * flyout is populated dynamically from the parent's schema via
 * ``workspace.registerToolboxCategoryCallback('PARENT_OVERRIDES', ...)``
 * in StrategyEditor.jsx.
 */
export const EXTEND_TOOLBOX_XML = `
<xml xmlns="https://developers.google.com/blockly/xml">
  <category name="Pre — Cuándo" colour="330">
    <block type="gd_pre_rule"></block>
  </category>
  <category name="Pre — Acciones" colour="330">
    <block type="gd_set_data"></block>
    <block type="gd_veto"></block>
  </category>
  <category name="Post — Cuándo" colour="60">
    <block type="gd_post_rule"></block>
  </category>
  <category name="Post — Acciones" colour="60">
    <block type="gd_set_points"></block>
    <block type="gd_set_case_name"></block>
  </category>
  <category name="Padre" colour="290">
    <block type="gd_field_parent"></block>
  </category>
  <category name="Overrides padre" colour="20" custom="PARENT_OVERRIDES">
  </category>
  <category name="Compara" colour="180">
    <block type="gd_compare"></block>
    <block type="gd_and"></block>
    <block type="gd_or"></block>
    <block type="gd_not"></block>
  </category>
  <category name="Campos" colour="290">
    <block type="gd_field"></block>
    <block type="gd_field_data"></block>
  </category>
  <category name="Calcula" colour="230">
    <block type="gd_arith"></block>
    <block type="gd_func_call"></block>
  </category>
  <category name="Valores" colour="330">
    <block type="gd_literal_number"></block>
    <block type="gd_literal_text"></block>
  </category>
  <category name="Asigna (callback)" colour="0">
    <block type="gd_set_callback_data"></block>
  </category>
</xml>
`.trim()

/**
 * Sprint 10: refresh the cached ``t`` reference and re-tooltip every
 * existing block. Called by the editor when the language changes.
 * Updates the prototype's tooltip via re-running each ``init()``-like
 * setter on the live blocks, which is the cheapest way to push the
 * new strings into Blockly without re-injecting the workspace.
 */
export function refreshBlockI18n(workspace, tFn) {
  if (tFn) _t = tFn
  if (!workspace) return
  for (const block of workspace.getAllBlocks(false)) {
    const tip = tooltip(block.type)
    if (tip) block.setTooltip(tip)
  }
}
