// Sprint 5: render the interpreter execution trace as a tree that mirrors
// the blocks the designer built, instead of the old flat list of JSON.
//
// The backend trace is a flat array of { nodeId, type, value, branch }
// entries - one per AST node the interpreter touched. On its own that's
// hard to read. Here we walk the *AST* (the exact structure on the canvas)
// and annotate each node with its trace outcome, so a designer sees which
// rule's condition was true/false and which rule actually granted points
// ("Disparó"). The AST is the one simulated (handleSimulate stores it
// alongside the result), so node ids line up 1:1 with the trace.

import React from 'react'
import PropTypes from 'prop-types'
import { useTranslation } from 'react-i18next'
import { CBadge } from '@coreui/react'

import GlossaryHint from './glossary/GlossaryHint'

// Shared prop shapes. ``byId`` is a Map(nodeId → trace entry); the AST/trace
// node objects are free-form (the DSL grammar is open-ended), so they're
// typed as plain objects.
const TRACE_ENTRY = PropTypes.object
const AST_NODE = PropTypes.object
const BY_ID = PropTypes.instanceOf(Map)

// Render an expression node (field / literal / arith / func_call) as a
// compact human-readable string. Conditions are handled separately by
// ConditionNode; this is only for the leaf operands.
function exprToText(node) {
  if (!node || typeof node !== 'object') return '∅'
  switch (node.type) {
    case 'field':
      return node.path || '∅'
    case 'literal':
      return JSON.stringify(node.value)
    case 'arith':
      return `(${exprToText(node.left)} ${node.op} ${exprToText(node.right)})`
    case 'func_call':
      return `${node.name}(${(node.args || []).map(exprToText).join(', ')})`
    default:
      return node.type || '∅'
  }
}

// Truth pill for a condition node, driven by the trace value (boolean).
// Returns null when the node wasn't reached (short-circuited away), so the
// tree stays honest about what the interpreter actually evaluated.
function TruthPill({ entry, t }) {
  if (!entry || typeof entry.value !== 'boolean') return null
  return entry.value ? (
    <CBadge color="success" className="ms-1">
      {t('simulate.tree.true')}
    </CBadge>
  ) : (
    <CBadge color="secondary" className="ms-1">
      {t('simulate.tree.false')}
    </CBadge>
  )
}

function ConditionNode({ node, byId, t }) {
  if (!node) return <span className="text-medium-emphasis">-</span>
  const entry = byId.get(node.id)

  if (node.type === 'and' || node.type === 'or') {
    const label = node.type === 'and' ? t('simulate.tree.and') : t('simulate.tree.or')
    return (
      <div>
        <span className="fw-semibold">{label}</span>
        <TruthPill entry={entry} t={t} />
        <ul className="mb-0 ps-3" style={{ listStyleType: 'circle' }}>
          {(node.args || []).map((arg, i) => (
            <li key={arg?.id || i}>
              <ConditionNode node={arg} byId={byId} t={t} />
            </li>
          ))}
        </ul>
      </div>
    )
  }

  if (node.type === 'not') {
    return (
      <div>
        <span className="fw-semibold">{t('simulate.tree.not')}</span>
        <TruthPill entry={entry} t={t} />
        <ul className="mb-0 ps-3" style={{ listStyleType: 'circle' }}>
          <li>
            <ConditionNode node={node.arg} byId={byId} t={t} />
          </li>
        </ul>
      </div>
    )
  }

  if (node.type === 'compare') {
    return (
      <span>
        <code>
          {exprToText(node.left)} {node.op} {exprToText(node.right)}
        </code>
        <TruthPill entry={entry} t={t} />
      </span>
    )
  }

  // Bare expression used directly as a condition (e.g. a literal true).
  return (
    <span>
      <code>{exprToText(node)}</code>
      <TruthPill entry={entry} t={t} />
    </span>
  )
}

// One executed/skipped statement inside a branch. ``decisiveId`` is the
// nodeId of the statement that set the final points (assign_points/veto),
// which we highlight as the outcome of the whole run.
function StatementNode({ node, byId, t, decisiveId }) {
  if (!node) return null
  const entry = byId.get(node.id)
  const executed = entry !== undefined
  const isDecisive = node.id === decisiveId

  let detail
  switch (node.type) {
    case 'assign_points':
      detail = t('simulate.tree.assignPoints', {
        points: executed ? entry.value : exprToText(node.value),
        caseName: node.case_name,
      })
      break
    case 'veto':
      detail = t('simulate.tree.veto', { caseName: node.case_name })
      break
    case 'set_points':
      detail = t('simulate.tree.setPoints', {
        value: executed ? entry.value : exprToText(node.value),
      })
      break
    case 'set_case_name':
      detail = t('simulate.tree.setCaseName', {
        value: executed ? entry.value : exprToText(node.value),
      })
      break
    case 'set_callback_data':
      detail = t('simulate.tree.setCallbackData', {
        key: node.key,
        value: executed ? JSON.stringify(entry.value) : exprToText(node.value),
      })
      break
    case 'set_data':
      detail = t('simulate.tree.setData', {
        key: node.key,
        value: executed ? JSON.stringify(entry.value) : exprToText(node.value),
      })
      break
    default:
      detail = t(`trace.types.${node.type}`, { defaultValue: node.type })
  }

  return (
    <li
      className={isDecisive ? 'fw-semibold text-success' : executed ? '' : 'text-medium-emphasis'}
    >
      {detail}
      {!executed && (
        <span className="ms-1 text-medium-emphasis">({t('simulate.tree.notRun')})</span>
      )}
    </li>
  )
}

function BranchStatements({ statements, byId, t, decisiveId }) {
  if (!statements || statements.length === 0) {
    return <div className="small text-medium-emphasis">{t('simulate.tree.emptyBranch')}</div>
  }
  return (
    <ul className="mb-0 ps-3">
      {statements.map((s, i) => (
        <li key={s?.id || i} style={{ listStyle: 'none' }}>
          <ul className="mb-0 ps-0" style={{ listStyle: 'none' }}>
            <StatementNode node={s} byId={byId} t={t} decisiveId={decisiveId} />
          </ul>
        </li>
      ))}
    </ul>
  )
}

// Map a rule's trace entry to which branch actually ran. Returns one of
// 'match' | { elseIf: index } | 'else' | 'skip' | null (not evaluated).
function ranBranch(entry) {
  if (!entry) return null
  const b = entry.branch
  if (b === 'match') return 'match'
  if (b === 'else') return 'else'
  if (b === 'skip') return 'skip'
  if (typeof b === 'string' && b.startsWith('elseif:')) {
    return { elseIf: Number(b.split(':')[1]) }
  }
  return null
}

function RuleNode({ rule, index, byId, t, decisiveId }) {
  const entry = byId.get(rule.id)
  const branch = ranBranch(entry)
  const evaluated = entry !== undefined

  // Statements of the branch that ran (used to decide if THIS rule fired).
  let ranStatements = []
  if (branch === 'match') ranStatements = rule.then
  else if (branch === 'else') ranStatements = rule.else
  else if (branch && branch.elseIf != null) {
    ranStatements = (rule.else_if || [])[branch.elseIf]?.then
  }
  const fired = (ranStatements || []).some((s) => s && s.id === decisiveId)

  // Outcome label for the rule header.
  let outcome
  let outcomeColor
  if (!evaluated) {
    outcome = t('simulate.tree.ruleNotEvaluated')
    outcomeColor = 'light'
  } else if (branch === 'match') {
    outcome = t('simulate.tree.ruleMatched')
    outcomeColor = 'success'
  } else if (branch && branch.elseIf != null) {
    outcome = t('simulate.tree.ruleElseIfMatched', { n: branch.elseIf + 1 })
    outcomeColor = 'info'
  } else if (branch === 'else') {
    outcome = t('simulate.tree.ruleElse')
    outcomeColor = 'info'
  } else {
    outcome = t('simulate.tree.ruleSkipped')
    outcomeColor = 'secondary'
  }

  return (
    <div
      className="mb-2 p-2 rounded"
      style={{
        borderLeft: `3px solid var(--cui-${fired ? 'success' : evaluated ? 'border-color' : 'border-color-translucent'})`,
        background: fired ? 'var(--cui-success-bg-subtle)' : 'var(--cui-tertiary-bg)',
      }}
    >
      <div className="d-flex justify-content-between align-items-center mb-1">
        <span className="small fw-semibold">{t('simulate.tree.ruleLabel', { n: index + 1 })}</span>
        <span>
          {fired && (
            <CBadge color="success" className="me-1">
              {t('simulate.tree.fired')}
            </CBadge>
          )}
          <CBadge color={outcomeColor} className={outcomeColor === 'light' ? 'text-dark' : ''}>
            {outcome}
          </CBadge>
        </span>
      </div>

      <div className="small mb-1">
        <span className="text-medium-emphasis me-1">{t('simulate.tree.when')}</span>
        <ConditionNode node={rule.when} byId={byId} t={t} />
      </div>

      {branch === 'match' && (
        <div className="small">
          <span className="text-medium-emphasis">{t('simulate.tree.then')}</span>
          <BranchStatements statements={rule.then} byId={byId} t={t} decisiveId={decisiveId} />
        </div>
      )}

      {(rule.else_if || []).map((eif, i) => {
        const eifRan = branch && branch.elseIf === i
        return (
          <div className="small mt-1" key={i}>
            <span className="text-medium-emphasis me-1">
              {t('simulate.tree.elseIf', { n: i + 1 })}
            </span>
            <ConditionNode node={eif.when} byId={byId} t={t} />
            {eifRan && (
              <BranchStatements statements={eif.then} byId={byId} t={t} decisiveId={decisiveId} />
            )}
          </div>
        )
      })}

      {branch === 'else' && rule.else && (
        <div className="small mt-1">
          <span className="text-medium-emphasis">{t('simulate.tree.else')}</span>
          <BranchStatements statements={rule.else} byId={byId} t={t} decisiveId={decisiveId} />
        </div>
      )}
    </div>
  )
}

export default function SimulationTracePanel({ ast, trace }) {
  const { t } = useTranslation('editor')

  if (!ast || !Array.isArray(trace)) return null

  // Last-write-wins: a node executes at most once per run, but building the
  // map defensively means we still render sensibly if that ever changes.
  const byId = new Map()
  for (const entry of trace) {
    if (entry && entry.nodeId != null) byId.set(entry.nodeId, entry)
  }

  // The decisive statement is the one that set the final points and halted
  // the run: assign_points (branch 'match') or veto (branch 'veto'). There
  // is at most one because both raise _DslHalt.
  const decisive = trace.find(
    (e) => e && ((e.type === 'assign_points' && e.branch === 'match') || e.type === 'veto'),
  )
  const decisiveId = decisive ? decisive.nodeId : null

  const rules = Array.isArray(ast.rules) ? ast.rules : []
  const preRules = Array.isArray(ast.pre_rules) ? ast.pre_rules : []
  const postRules = Array.isArray(ast.post_rules) ? ast.post_rules : []
  const hasAnything = rules.length || preRules.length || postRules.length || ast.default

  if (!hasAnything) {
    return (
      <p className="small text-medium-emphasis">
        {t('simulate.noTrace')}
        <GlossaryHint term="rule" />
      </p>
    )
  }

  const renderRuleList = (list) =>
    list.map((rule, i) => (
      <RuleNode
        key={rule?.id || i}
        rule={rule}
        index={i}
        byId={byId}
        t={t}
        decisiveId={decisiveId}
      />
    ))

  // The default branch fires only when no rule matched; surface it the same
  // way so a designer can see "fell through to default".
  const defaultEntry = ast.default ? byId.get(ast.default.id) : undefined

  return (
    <div>
      {preRules.length > 0 && (
        <>
          <div className="small fw-semibold mb-1">{t('simulate.tree.preRules')}</div>
          {renderRuleList(preRules)}
        </>
      )}

      {rules.length > 0 && renderRuleList(rules)}

      {ast.default && (
        <div
          className="mb-2 p-2 rounded"
          style={{
            borderLeft: `3px solid var(--cui-${defaultEntry ? 'success' : 'border-color-translucent'})`,
            background: defaultEntry ? 'var(--cui-success-bg-subtle)' : 'var(--cui-tertiary-bg)',
          }}
        >
          <div className="small fw-semibold mb-1">{t('simulate.tree.default')}</div>
          <ul className="mb-0 ps-3" style={{ listStyle: 'none' }}>
            <StatementNode node={ast.default} byId={byId} t={t} decisiveId={decisiveId} />
          </ul>
        </div>
      )}

      {postRules.length > 0 && (
        <>
          <div className="small fw-semibold mb-1 mt-2">{t('simulate.tree.postRules')}</div>
          {renderRuleList(postRules)}
        </>
      )}
    </div>
  )
}

TruthPill.propTypes = {
  entry: TRACE_ENTRY,
  t: PropTypes.func.isRequired,
}

ConditionNode.propTypes = {
  node: AST_NODE,
  byId: BY_ID.isRequired,
  t: PropTypes.func.isRequired,
}

StatementNode.propTypes = {
  node: AST_NODE,
  byId: BY_ID.isRequired,
  t: PropTypes.func.isRequired,
  decisiveId: PropTypes.string,
}

BranchStatements.propTypes = {
  statements: PropTypes.arrayOf(PropTypes.object),
  byId: BY_ID.isRequired,
  t: PropTypes.func.isRequired,
  decisiveId: PropTypes.string,
}

RuleNode.propTypes = {
  rule: AST_NODE.isRequired,
  index: PropTypes.number.isRequired,
  byId: BY_ID.isRequired,
  t: PropTypes.func.isRequired,
  decisiveId: PropTypes.string,
}

SimulationTracePanel.propTypes = {
  ast: AST_NODE,
  trace: PropTypes.arrayOf(PropTypes.object),
}
