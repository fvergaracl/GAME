// Sprint 8: data layer for the DSL glossary.
//
// Single source of truth for the concepts referenced from contextual
// popovers (GlossaryHint), the help button in the app header, the
// Library/Assignments tours and the related-concepts section of
// BlockHelpView. Each entry's user-visible strings live under the
// ``glossary`` i18n namespace — the data here only carries structural
// metadata (related concepts, optional pointer to the per-block doc).
//
// Adding a new term:
//   1. Append it to GLOSSARY_TERMS.
//   2. Add ``<id>.title`` + ``<id>.body`` to ``locales/{es,en}/glossary.json``.
//   3. (Optional) link Blockly blocks to it via BLOCK_TO_TERM.

export const GLOSSARY_TERMS = [
  // Rule structure
  { id: 'rule', related: ['preRule', 'postRule', 'caseName'], blockSlug: 'rule' },
  { id: 'preRule', related: ['rule', 'postRule', 'parentOverride'], blockSlug: 'pre-rule' },
  { id: 'postRule', related: ['rule', 'preRule', 'veto'], blockSlug: 'post-rule' },
  { id: 'veto', related: ['postRule', 'caseName'], blockSlug: 'veto' },
  // Output / payload
  { id: 'caseName', related: ['callbackData', 'rule'], blockSlug: 'set-case-name' },
  { id: 'callbackData', related: ['caseName', 'dataField'], blockSlug: 'set-callback-data' },
  { id: 'dataField', related: ['callbackData'], blockSlug: 'field-data' },
  // Extension model
  { id: 'parentStrategy', related: ['dslExtend', 'parentOverride'] },
  {
    id: 'parentOverride',
    related: ['parentStrategy', 'dslExtend'],
    blockSlug: 'parent-variable-override',
  },
  { id: 'dslFull', related: ['dslExtend'] },
  { id: 'dslExtend', related: ['dslFull', 'parentStrategy', 'parentOverride'] },
  // Lifecycle
  { id: 'lifecycle', related: ['draft', 'published', 'archived'] },
  { id: 'draft', related: ['published', 'archived', 'lifecycle'] },
  { id: 'published', related: ['draft', 'archived', 'lifecycle'] },
  { id: 'archived', related: ['draft', 'published', 'lifecycle'] },
  // Assignment model
  { id: 'assignment', related: ['published', 'parentStrategy'] },
]

export const GLOSSARY_INDEX = Object.fromEntries(GLOSSARY_TERMS.map((term) => [term.id, term]))

// Maps custom Blockly block types to the closest glossary entry so the
// right-click "Help" page can surface a related-concepts panel
// (complements C5 / HELP_URLS — Sprint 3 wires the per-block doc, this
// adds the conceptual cross-link).
export const BLOCK_TO_TERM = {
  gd_rule: 'rule',
  gd_rule_elseif: 'rule',
  gd_rule_else: 'rule',
  gd_field: 'dataField',
  gd_field_data: 'dataField',
  gd_field_parent: 'parentOverride',
  gd_parent_variable_override: 'parentOverride',
  gd_pre_rule: 'preRule',
  gd_post_rule: 'postRule',
  gd_veto: 'veto',
  gd_assign_points: 'caseName',
  gd_set_case_name: 'caseName',
  gd_set_callback_data: 'callbackData',
  gd_set_data: 'dataField',
  gd_set_points: 'postRule',
}

// Slug → glossary id, mirror of the blockSlug field on the data above.
// Used by BlockHelpView (which only has the slug, not the block type).
export const SLUG_TO_TERM = GLOSSARY_TERMS.reduce((acc, term) => {
  if (term.blockSlug) acc[term.blockSlug] = term.id
  return acc
}, {})
