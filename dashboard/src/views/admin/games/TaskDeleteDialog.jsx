// Sprint 3 (CRUD management) — delete a Task.
//
// Thin wrapper over the shared ConfirmDialog (a11y + busy handling included).
// Unlike a game delete there's no blast-radius to preview: the cascade
// (params + user-points rows) happens server-side and there's no meaningful
// sub-count to surface, so we just confirm and call deleteTask with the
// task's INTERNAL uuid (the DELETE route is keyed on it).

import React, { useState } from 'react'
import PropTypes from 'prop-types'
import { useTranslation } from 'react-i18next'

import { deleteTask } from '../../../api'
import { extractError } from '../../../utils/errors'
import { useToast } from '../../../components/Toast'
import ConfirmDialog from '../../../components/ConfirmDialog'

const TaskDeleteDialog = ({ visible, gameId, task, onCancel, onDeleted }) => {
  const { t } = useTranslation('management')
  const toast = useToast()
  const [deleting, setDeleting] = useState(false)

  const taskId = task?.id != null ? String(task.id) : null
  const externalTaskId = task?.externalTaskId || ''

  const handleConfirm = async () => {
    if (!taskId) return
    setDeleting(true)
    try {
      await deleteTask(gameId, taskId)
      toast.success(t('feedback.taskDeleted'))
      onDeleted?.()
    } catch (err) {
      toast.error(extractError(err, t('common.loadError')))
    } finally {
      setDeleting(false)
    }
  }

  return (
    <ConfirmDialog
      visible={visible}
      title={t('tasks.delete.title')}
      message={<p className="mb-0">{t('tasks.delete.message', { externalTaskId })}</p>}
      confirmLabel={t('tasks.delete.confirm')}
      confirmColor="danger"
      busy={deleting}
      onConfirm={handleConfirm}
      onCancel={onCancel}
    />
  )
}

TaskDeleteDialog.propTypes = {
  visible: PropTypes.bool,
  gameId: PropTypes.string,
  task: PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    externalTaskId: PropTypes.string,
  }),
  onCancel: PropTypes.func,
  onDeleted: PropTypes.func,
}

export default TaskDeleteDialog
