// Sprint 6: custom Blockly block definitions for the strategy DSL.
//
// Each block maps 1:1 to an AST node in app/engine/dsl_ast.py. The
// dropdowns are sourced from the whitelists mirror so they always show
// the same options the backend will accept.
//
// Why so many blocks (11) when the roadmap says "6-8"? The roadmap's
// 6-8 refers to *categories shown to the designer in the toolbox*
// (grouped via the toolbox XML). Internally Blockly needs a block per
// AST concept; combining them would require complex mutators that hurt
// edit-time UX. We trade a longer block list for simpler bindings.

import * as Blockly from 'blockly'

import {
  ARITH_OPS,
  COMPARE_OPS,
  FIELD_PATHS,
  FUNC_NAMES,
} from '../dsl/whitelists'

// Helper: build a [[label, value], ...] options list from a string array.
const optionsFromArray = (arr) => arr.map((v) => [v, v])

let _registered = false

/**
 * Register all DSL blocks with the Blockly registry. Idempotent — calling
 * this twice is a no-op (Blockly throws on duplicate block names).
 */
export function registerDslBlocks() {
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
        .appendField('cuando')
      this.appendStatementInput('THEN')
        .setCheck('Statement')
        .appendField('entonces')
      this.setColour(210)
      this.setTooltip('Una regla del scoring: si la condición se cumple, ejecuta las acciones.')
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
      this.setTooltip('Compara dos valores.')
    },
  }

  // ---- gd_and / gd_or (binary for MVP — mutator for variadic in S7) ------
  Blockly.Blocks.gd_and = {
    init() {
      this.appendValueInput('A').setCheck('Boolean').appendField('y')
      this.appendValueInput('B').setCheck('Boolean').appendField('y también')
      this.setOutput(true, 'Boolean')
      this.setInputsInline(true)
      this.setColour(150)
      this.setTooltip('Ambas condiciones deben cumplirse.')
    },
  }
  Blockly.Blocks.gd_or = {
    init() {
      this.appendValueInput('A').setCheck('Boolean').appendField('o')
      this.appendValueInput('B').setCheck('Boolean').appendField('o también')
      this.setOutput(true, 'Boolean')
      this.setInputsInline(true)
      this.setColour(150)
      this.setTooltip('Al menos una condición debe cumplirse.')
    },
  }

  // ---- gd_not ------------------------------------------------------------
  Blockly.Blocks.gd_not = {
    init() {
      this.appendValueInput('ARG').setCheck('Boolean').appendField('no')
      this.setOutput(true, 'Boolean')
      this.setColour(150)
      this.setTooltip('Niega la condición.')
    },
  }

  // ---- gd_field ----------------------------------------------------------
  // Picks a whitelisted analytic path. ``data.<key>`` is handled by the
  // separate gd_field_data block so the dropdown doesn't drown the
  // designer in arbitrary keys.
  Blockly.Blocks.gd_field = {
    init() {
      this.appendDummyInput()
        .appendField('campo')
        .appendField(
          new Blockly.FieldDropdown(optionsFromArray(FIELD_PATHS)),
          'PATH',
        )
      this.setOutput(true, 'Number')
      this.setColour(290)
      this.setTooltip('Lee un campo precalculado de la analítica o del request.')
    },
  }

  // ---- gd_field_data -----------------------------------------------------
  // Dynamic ``data.<key>`` reader for caller-supplied event payload.
  Blockly.Blocks.gd_field_data = {
    init() {
      this.appendDummyInput()
        .appendField('data.')
        .appendField(
          new Blockly.FieldTextInput('my_key', (value) => {
            // Mirror the backend regex: [A-Za-z0-9_]+
            return /^[A-Za-z0-9_]+$/.test(value) ? value : null
          }),
          'KEY',
        )
      this.setOutput(true, ['Number', 'String', 'Boolean'])
      this.setColour(290)
      this.setTooltip('Lee data.<clave> del payload del evento.')
    },
  }

  // ---- gd_literal_number / gd_literal_text -------------------------------
  Blockly.Blocks.gd_literal_number = {
    init() {
      this.appendDummyInput()
        .appendField(new Blockly.FieldNumber(0), 'VALUE')
      this.setOutput(true, 'Number')
      this.setColour(330)
      this.setTooltip('Un número fijo.')
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
      this.setTooltip('Un texto fijo.')
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
      this.setTooltip('Operación aritmética (+, -, *, /, min, max).')
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
      this.setTooltip('Función: int(x) o clamp(value, lo, hi).')
      this._rebuildArgs('int')
    },
    _rebuildArgs(name) {
      // Tear down any existing arg slots.
      for (const inputName of ['VALUE', 'LO', 'HI']) {
        if (this.getInput(inputName)) this.removeInput(inputName)
      }
      if (name === 'int') {
        this.appendValueInput('VALUE').setCheck('Number').appendField('valor')
      } else if (name === 'clamp') {
        this.appendValueInput('VALUE').setCheck('Number').appendField('valor')
        this.appendValueInput('LO').setCheck('Number').appendField('min')
        this.appendValueInput('HI').setCheck('Number').appendField('max')
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
        .appendField('asignar puntos')
      this.appendDummyInput()
        .appendField('caso')
        .appendField(new Blockly.FieldTextInput('default'), 'CASE_NAME')
      this.setPreviousStatement(true, 'Statement')
      // No nextStatement: assign_points halts the rule.
      this.setColour(60)
      this.setTooltip('Asigna puntos y etiqueta el resultado con un caso.')
    },
  }

  // ---- gd_set_callback_data ----------------------------------------------
  Blockly.Blocks.gd_set_callback_data = {
    init() {
      this.appendDummyInput()
        .appendField('guardar dato')
        .appendField(new Blockly.FieldTextInput('clave'), 'KEY')
      this.appendValueInput('VALUE')
        .setCheck(['Number', 'String', 'Boolean'])
        .appendField('=')
      this.setInputsInline(true)
      this.setPreviousStatement(true, 'Statement')
      this.setNextStatement(true, 'Statement')
      this.setColour(0)
      this.setTooltip('Adjunta dato adicional al resultado.')
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
        .appendField('PRE — cuando')
      this.appendStatementInput('THEN')
        .setCheck('Statement')
        .appendField('entonces')
      this.setColour(330)
      this.setTooltip('Se ejecuta ANTES del padre. Puede mutar data o vetar.')
    },
  }

  // ---- gd_post_rule ------------------------------------------------------
  Blockly.Blocks.gd_post_rule = {
    init() {
      this.appendValueInput('WHEN')
        .setCheck(['Boolean', 'Number'])
        .appendField('POST — cuando')
      this.appendStatementInput('THEN')
        .setCheck('Statement')
        .appendField('entonces')
      this.setColour(60)
      this.setTooltip(
        'Se ejecuta DESPUÉS del padre. Lee parent.points / parent.case_name.',
      )
    },
  }

  // ---- gd_set_data -------------------------------------------------------
  // Mutates the working_data dict the parent built-in will receive. Key
  // must be alphanumeric+underscore so it's addressable via data.<key>.
  Blockly.Blocks.gd_set_data = {
    init() {
      this.appendDummyInput()
        .appendField('set data')
        .appendField(new Blockly.FieldTextInput('mi_clave'), 'KEY')
      this.appendValueInput('VALUE')
        .setCheck(['Number', 'String', 'Boolean'])
        .appendField('=')
      this.setInputsInline(true)
      this.setPreviousStatement(true, 'Statement')
      this.setNextStatement(true, 'Statement')
      this.setColour(330)
      this.setTooltip('Escribe data.<clave> antes de llamar al padre.')
    },
  }

  // ---- gd_veto -----------------------------------------------------------
  // Terminator: when this fires, the parent and post_rules never run.
  // The final result is (0, case_name).
  Blockly.Blocks.gd_veto = {
    init() {
      this.appendDummyInput()
        .appendField('VETO — caso')
        .appendField(new Blockly.FieldTextInput('TooEarly'), 'CASE_NAME')
      this.setPreviousStatement(true, 'Statement')
      // No nextStatement: veto halts the entire pipeline.
      this.setColour(0)
      this.setTooltip(
        'Aborta toda la asignación. Padre y post-reglas no se ejecutan.',
      )
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
        .appendField('set puntos')
      this.setPreviousStatement(true, 'Statement')
      this.setNextStatement(true, 'Statement')
      this.setColour(60)
      this.setTooltip('Sobrescribe los puntos del padre.')
    },
  }

  // ---- gd_set_case_name --------------------------------------------------
  Blockly.Blocks.gd_set_case_name = {
    init() {
      this.appendValueInput('VALUE')
        .setCheck('String')
        .appendField('set caseName')
      this.setPreviousStatement(true, 'Statement')
      this.setNextStatement(true, 'Statement')
      this.setColour(60)
      this.setTooltip('Sobrescribe el caseName del padre.')
    },
  }

  // ---- gd_field_parent ---------------------------------------------------
  // Reads parent.points or parent.case_name. Only valid in post_rules —
  // the client-side validator catches mis-placement.
  Blockly.Blocks.gd_field_parent = {
    init() {
      this.appendDummyInput()
        .appendField('padre.')
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
      this.setTooltip(
        'Lee el resultado del padre. Sólo válido dentro de POST.',
      )
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
        .appendField('override')
        .appendField(
          new Blockly.FieldTextInput('variable_basic_points'),
          'VARIABLE',
        )
        .appendField('=')
        .appendField(new Blockly.FieldTextInput('1'), 'VALUE')
      this.setColour(20)
      this.setTooltip(
        'Sobrescribe un variable_* del padre antes de su ejecución.',
      )
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
