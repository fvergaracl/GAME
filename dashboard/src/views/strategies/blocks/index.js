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

// Documentation URLs per block. Used as helpUrl so the right-click menu
// surfaces a "Help" entry. Internal hash links are placeholders — when
// the docs site exists they should be swapped for real URLs.
const HELP_URLS = {
  gd_rule: '#/docs/strategy-blocks/rule',
  gd_compare: '#/docs/strategy-blocks/compare',
  gd_and: '#/docs/strategy-blocks/and',
  gd_or: '#/docs/strategy-blocks/or',
  gd_not: '#/docs/strategy-blocks/not',
  gd_field: '#/docs/strategy-blocks/field',
  gd_field_data: '#/docs/strategy-blocks/field-data',
  gd_literal_number: '#/docs/strategy-blocks/literal-number',
  gd_literal_text: '#/docs/strategy-blocks/literal-text',
  gd_arith: '#/docs/strategy-blocks/arith',
  gd_func_call: '#/docs/strategy-blocks/func-call',
  gd_assign_points: '#/docs/strategy-blocks/assign-points',
  gd_set_callback_data: '#/docs/strategy-blocks/set-callback-data',
  gd_pre_rule: '#/docs/strategy-blocks/pre-rule',
  gd_post_rule: '#/docs/strategy-blocks/post-rule',
  gd_set_data: '#/docs/strategy-blocks/set-data',
  gd_veto: '#/docs/strategy-blocks/veto',
  gd_set_points: '#/docs/strategy-blocks/set-points',
  gd_set_case_name: '#/docs/strategy-blocks/set-case-name',
  gd_field_parent: '#/docs/strategy-blocks/field-parent',
  gd_parent_variable_override: '#/docs/strategy-blocks/parent-variable-override',
}

// Look up a localised label / tooltip with a Spanish fallback so the
// blocks render usable text even before i18next has initialised (e.g.
// during a unit-test snapshot).
const FALLBACK_LABELS = {
  when: 'cuando',
  then: 'entonces',
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

  // ---- gd_rule -----------------------------------------------------------
  // Statement-shaped root that holds one ``when`` condition and a stack of
  // ``then`` statements. Top-level on the workspace; not connectable to
  // anything else.
  Blockly.Blocks.gd_rule = {
    init() {
      // ``WHEN`` accepts Boolean OR Number so a bare ``literal true`` or
      // a numeric field (used as truthy) can be plugged directly without
      // a compare wrapper, mirroring the backend interpreter at
      // app/engine/dsl_interpreter.py:302-304 ("Allow bare expressions
      // as conditions").
      this.appendValueInput('WHEN')
        .setCheck(['Boolean', 'Number'])
        .appendField(label('when'))
      this.appendStatementInput('THEN')
        .setCheck('Statement')
        .appendField(label('then'))
      this.setColour(210)
      this.setTooltip(tooltip('gd_rule'))
      this.setHelpUrl(HELP_URLS.gd_rule)
    },
  }

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
  // Same shape as gd_rule but emits into pre_rules[]. Visually
  // distinguished by colour so the designer sees at a glance which
  // section a rule belongs to.
  Blockly.Blocks.gd_pre_rule = {
    init() {
      this.appendValueInput('WHEN')
        .setCheck(['Boolean', 'Number'])
        .appendField(label('preWhen'))
      this.appendStatementInput('THEN')
        .setCheck('Statement')
        .appendField(label('then'))
      this.setColour(330)
      this.setTooltip(tooltip('gd_pre_rule'))
      this.setHelpUrl(HELP_URLS.gd_pre_rule)
    },
  }

  // ---- gd_post_rule ------------------------------------------------------
  Blockly.Blocks.gd_post_rule = {
    init() {
      this.appendValueInput('WHEN')
        .setCheck(['Boolean', 'Number'])
        .appendField(label('postWhen'))
      this.appendStatementInput('THEN')
        .setCheck('Statement')
        .appendField(label('then'))
      this.setColour(60)
      this.setTooltip(tooltip('gd_post_rule'))
      this.setHelpUrl(HELP_URLS.gd_post_rule)
    },
  }

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
