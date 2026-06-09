// Delete a Game with a blast-radius preview.
//
// Deleting a game cascades to its tasks (and their params) server-side, so
// before asking the admin to confirm we fetch the game's tasks and show how
// many will go with it. The count is loaded lazily when the dialog opens -
// the list view doesn't carry task counts, and fetching per-row up front
// would be wasteful for a confirmation the user may never trigger.
//
// We render ConfirmDialog (the shared, a11y-wired confirm modal) rather than
// hand-rolling a modal: it already flips initial focus to Cancel for
// destructive (danger) actions and blocks dismissal while busy. A failure to
// count tasks is non-blocking - the user can still delete; we just omit the
// blast-radius line rather than trapping them behind a transient read error.

import React, { useEffect, useState } from 'react'
import PropTypes from 'prop-types'
import { useTranslation } from 'react-i18next'

import { deleteGame, listGameTasks } from '../../../api'
import { extractError } from '../../../utils/errors'
import { useToast } from '../../../components/Toast'
import ConfirmDialog from '../../../components/ConfirmDialog'

const GameDeleteDialog = ({ visible, game, onCancel, onDeleted }) => {
  const { t } = useTranslation('management')
  const toast = useToast()

  const [taskCount, setTaskCount] = useState(null)
  const [countingTasks, setCountingTasks] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const gameId = game?.gameId != null ? String(game.gameId) : null
  const externalGameId = game?.externalGameId || ''

  // On open, count the tasks that would cascade-delete. Best-effort: a read
  // failure just hides the blast-radius line, it doesn't block the delete.
  useEffect(() => {
    if (!visible || !gameId) return undefined
    let cancelled = false
    setTaskCount(null)
    setCountingTasks(true)
    listGameTasks(gameId)
      .then((response) => {
        if (cancelled) return
        setTaskCount((response?.items || []).length)
      })
      .catch(() => {
        if (!cancelled) setTaskCount(null)
      })
      .finally(() => {
        if (!cancelled) setCountingTasks(false)
      })
    return () => {
      cancelled = true
    }
  }, [visible, gameId])

  const handleConfirm = async () => {
    if (!gameId) return
    setDeleting(true)
    try {
      await deleteGame(gameId)
      toast.success(t('feedback.gameDeleted'))
      onDeleted?.()
    } catch (err) {
      toast.error(extractError(err, t('common.loadError')))
    } finally {
      setDeleting(false)
    }
  }

  const message = (
    <>
      <p className="mb-2">{t('games.delete.message', { externalGameId })}</p>
      {countingTasks && (
        <p className="mb-0 text-medium-emphasis small">{t('games.delete.checkingTasks')}</p>
      )}
      {!countingTasks && taskCount > 0 && (
        <p className="mb-0 text-danger">{t('games.delete.blastRadius', { count: taskCount })}</p>
      )}
    </>
  )

  return (
    <ConfirmDialog
      visible={visible}
      title={t('games.delete.title')}
      message={message}
      confirmLabel={t('games.delete.confirm')}
      confirmColor="danger"
      busy={deleting}
      onConfirm={handleConfirm}
      onCancel={onCancel}
    />
  )
}

GameDeleteDialog.propTypes = {
  visible: PropTypes.bool,
  game: PropTypes.shape({
    gameId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    externalGameId: PropTypes.string,
  }),
  onCancel: PropTypes.func,
  onDeleted: PropTypes.func,
}

export default GameDeleteDialog
