// Sprint 6 — strategy usage / reverse-lookup modal.
//
// "¿Dónde se usa esta estrategia?" Opened from the library, it lists the
// games and tasks currently assigned to a specific strategy version
// (GET /strategies/custom/{id}/usage) so an admin can see the blast
// radius before archiving or rolling back — and, from the same place,
// reassign every consumer to another strategy in one bulk action.

import React, { useCallback, useEffect, useState } from 'react'
import PropTypes from 'prop-types'
import {
  CAlert,
  CBadge,
  CButton,
  CListGroup,
  CListGroupItem,
  CModal,
  CModalBody,
  CModalFooter,
  CModalHeader,
  CModalTitle,
  CProgress,
  CSpinner,
} from '@coreui/react'

import { getStrategyUsage, patchGameStrategy, patchTaskStrategy } from '../../api'
import StrategyPickerModal from './StrategyPickerModal'

const extractError = (err, fallback) => err?.response?.data?.detail || err?.message || fallback

const StrategyUsageModal = ({ visible, strategyId, strategyName, onClose, onReassigned }) => {
  const [usage, setUsage] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  const [pickerOpen, setPickerOpen] = useState(false)
  const [progress, setProgress] = useState(null)
  const [actionError, setActionError] = useState(null)
  const [actionSuccess, setActionSuccess] = useState(null)

  const load = useCallback(() => {
    if (!strategyId) return undefined
    let cancelled = false
    setIsLoading(true)
    setError(null)
    getStrategyUsage(strategyId)
      .then((data) => {
        if (!cancelled) setUsage(data)
      })
      .catch((err) => {
        if (!cancelled) setError(extractError(err, 'No se pudo cargar el uso de la estrategia.'))
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [strategyId])

  useEffect(() => {
    if (!visible) {
      // Reset transient state when the modal closes so a re-open starts clean.
      setUsage(null)
      setActionError(null)
      setActionSuccess(null)
      setProgress(null)
      return undefined
    }
    return load()
  }, [visible, load])

  const reassignAll = useCallback(
    async (newStrategyId) => {
      if (!usage) return
      setActionError(null)
      setActionSuccess(null)
      const games = usage.games || []
      const tasks = usage.tasks || []
      const total = games.length + tasks.length
      setProgress({ total, done: 0 })
      const failed = []
      let done = 0
      for (const game of games) {
        try {
          await patchGameStrategy(game.gameId, newStrategyId)
        } catch (err) {
          failed.push(`game ${game.externalGameId || game.gameId} (${extractError(err, 'error')})`)
        }
        done += 1
        setProgress({ total, done })
      }
      for (const task of tasks) {
        try {
          await patchTaskStrategy(task.gameId, task.taskId, newStrategyId)
        } catch (err) {
          failed.push(`task ${task.externalTaskId || task.taskId} (${extractError(err, 'error')})`)
        }
        done += 1
        setProgress({ total, done })
      }
      setProgress(null)
      const ok = total - failed.length
      setActionSuccess(`${ok} de ${total} consumidores reasignados.`)
      if (failed.length > 0) {
        setActionError(`${failed.length} fallaron: ${failed.join('; ')}`)
      }
      load()
      if (onReassigned) onReassigned()
    },
    [usage, load, onReassigned],
  )

  const counts = usage
    ? {
        games: usage.gameCount ?? usage.games?.length ?? 0,
        tasks: usage.taskCount ?? usage.tasks?.length ?? 0,
      }
    : { games: 0, tasks: 0 }
  const hasConsumers = counts.games + counts.tasks > 0

  return (
    <>
      <CModal visible={visible} onClose={onClose} size="lg" scrollable>
        <CModalHeader>
          <CModalTitle>¿Dónde se usa{strategyName ? ` «${strategyName}»` : ''}?</CModalTitle>
        </CModalHeader>
        <CModalBody>
          {isLoading && (
            <div className="d-flex justify-content-center py-4">
              <CSpinner />
            </div>
          )}
          {error && <CAlert color="danger">{error}</CAlert>}
          {actionError && (
            <CAlert color="warning" dismissible onClose={() => setActionError(null)}>
              {actionError}
            </CAlert>
          )}
          {actionSuccess && (
            <CAlert color="success" dismissible onClose={() => setActionSuccess(null)}>
              {actionSuccess}
            </CAlert>
          )}

          {!isLoading && usage && (
            <>
              <p className="text-medium-emphasis">
                Esta versión está asignada a <strong>{counts.games}</strong> game
                {counts.games === 1 ? '' : 's'} y <strong>{counts.tasks}</strong> task
                {counts.tasks === 1 ? '' : 's'}.
                {hasConsumers
                  ? ' Reasignarlos los moverá a otra estrategia.'
                  : ' Nadie la usa: es seguro archivarla.'}
              </p>

              {counts.games > 0 && (
                <>
                  <h6 className="mt-3">
                    Games <CBadge color="success">{counts.games}</CBadge>
                  </h6>
                  <CListGroup className="mb-2">
                    {usage.games.map((game) => (
                      <CListGroupItem
                        key={game.gameId}
                        className="d-flex justify-content-between align-items-center"
                      >
                        <code>{game.externalGameId || game.gameId}</code>
                        <CBadge color="secondary">{game.platform || '—'}</CBadge>
                      </CListGroupItem>
                    ))}
                  </CListGroup>
                </>
              )}

              {counts.tasks > 0 && (
                <>
                  <h6 className="mt-3">
                    Tasks <CBadge color="info">{counts.tasks}</CBadge>
                  </h6>
                  <CListGroup>
                    {usage.tasks.map((task) => (
                      <CListGroupItem key={task.taskId}>
                        <code>{task.externalTaskId || task.taskId}</code>
                        {task.externalGameId && (
                          <small className="text-medium-emphasis ms-2">
                            en {task.externalGameId}
                          </small>
                        )}
                      </CListGroupItem>
                    ))}
                  </CListGroup>
                </>
              )}

              {progress && (
                <div className="mt-3">
                  <CProgress
                    value={progress.total ? (progress.done / progress.total) * 100 : 100}
                  />
                  <small className="text-medium-emphasis">
                    {progress.done} / {progress.total}
                  </small>
                </div>
              )}
            </>
          )}
        </CModalBody>
        <CModalFooter>
          <CButton color="secondary" variant="outline" onClick={onClose} disabled={!!progress}>
            Cerrar
          </CButton>
          {hasConsumers && (
            <CButton color="primary" onClick={() => setPickerOpen(true)} disabled={!!progress}>
              Reasignar consumidores
            </CButton>
          )}
        </CModalFooter>
      </CModal>

      <StrategyPickerModal
        visible={pickerOpen}
        currentStrategyId={usage?.strategyId}
        onClose={() => setPickerOpen(false)}
        onSelect={(newStrategyId) => {
          setPickerOpen(false)
          reassignAll(newStrategyId)
        }}
      />
    </>
  )
}

StrategyUsageModal.propTypes = {
  visible: PropTypes.bool.isRequired,
  strategyId: PropTypes.string,
  strategyName: PropTypes.string,
  onClose: PropTypes.func.isRequired,
  onReassigned: PropTypes.func,
}

StrategyUsageModal.defaultProps = {
  strategyId: null,
  strategyName: null,
  onReassigned: null,
}

export default StrategyUsageModal
