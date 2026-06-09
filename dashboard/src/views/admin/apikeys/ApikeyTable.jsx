// Sprint 4 (CRUD management) - API key listing with revoke.
//
// The table is the only place an admin closes out an API key's lifecycle.
// Revocation is irreversible server-side (the row stays but flips to
// active=false and the auth cache entry is dropped), so the trash action
// routes through the shared ConfirmDialog rather than firing on a single
// click. After a successful revoke we toast and ask the parent to refresh;
// the key reappears marked "Revoked" via the status badge, which is why the
// previous non-functional view/edit placeholder buttons were dropped -
// revoke is the only action the backend actually supports here.

import React, { useState } from 'react'
import {
  CBadge,
  CButton,
  CCard,
  CCardBody,
  CCardHeader,
  CCol,
  CRow,
  CTable,
  CTableBody,
  CTableHead,
  CTableHeaderCell,
  CTableRow,
  CTableDataCell,
  CPagination,
  CPaginationItem,
} from '@coreui/react'
import { cilTrash } from '@coreui/icons'
import CIcon from '@coreui/icons-react'
import propTypes from 'prop-types'
import { useTranslation } from 'react-i18next'

import { deleteApiKey } from '../../../api'
import { extractError } from '../../../utils/errors'
import { useToast } from '../../../components/Toast'
import ConfirmDialog from '../../../components/ConfirmDialog'

const ITEMS_PER_PAGE = 10

const ApiKeyTable = ({ apiKeys, onRevoked }) => {
  const { t } = useTranslation('apikeys')
  // ConfirmDialog + feedback copy live in the `management` namespace, shared
  // with the games/tasks dialogs so revoke matches their look and wording.
  const { t: tm } = useTranslation('management')
  const toast = useToast()

  const [currentPage, setCurrentPage] = useState(1)
  // The row awaiting confirmation, plus an in-flight guard so the dialog can
  // show a spinner and block a double-submit.
  const [revokeTarget, setRevokeTarget] = useState(null)
  const [revoking, setRevoking] = useState(false)

  const totalPages = Math.max(1, Math.ceil(apiKeys.length / ITEMS_PER_PAGE))
  // Clamp: a revoke-driven refresh can shrink the list below the open page.
  const page = Math.min(currentPage, totalPages)
  const currentApiKeys = apiKeys.slice((page - 1) * ITEMS_PER_PAGE, page * ITEMS_PER_PAGE)

  const handlePageChange = (pageNumber) => {
    setCurrentPage(pageNumber)
  }

  const handleConfirmRevoke = async () => {
    if (!revokeTarget) return
    setRevoking(true)
    try {
      await deleteApiKey(revokeTarget.apiKey)
      toast.success(tm('feedback.apiKeyRevoked'))
      setRevokeTarget(null)
      onRevoked?.()
    } catch (err) {
      toast.error(extractError(err, tm('feedback.apiKeyRevokeError')))
    } finally {
      setRevoking(false)
    }
  }

  return (
    <CRow>
      <CCol xs={12}>
        <CCard className="mb-4">
          <CCardHeader>
            <strong>{t('table.headerTitle')}</strong> <small>{t('table.headerSubtitle')}</small>
          </CCardHeader>
          <CCardBody>
            <p className="text-body-secondary small">{t('table.intro')}</p>

            <CTable striped responsive align="middle">
              <CTableHead>
                <CTableRow>
                  <CTableHeaderCell scope="col">#</CTableHeaderCell>
                  <CTableHeaderCell scope="col">{t('table.col.apiKey')}</CTableHeaderCell>
                  <CTableHeaderCell scope="col">{t('table.col.client')}</CTableHeaderCell>
                  <CTableHeaderCell scope="col">{t('table.col.description')}</CTableHeaderCell>
                  <CTableHeaderCell scope="col">{t('table.col.createdAt')}</CTableHeaderCell>
                  <CTableHeaderCell scope="col">{t('table.col.status')}</CTableHeaderCell>
                  <CTableHeaderCell scope="col" className="text-end">
                    {t('table.col.actions')}
                  </CTableHeaderCell>
                </CTableRow>
              </CTableHead>
              <CTableBody>
                {currentApiKeys.length === 0 && (
                  <CTableRow>
                    <CTableDataCell colSpan={7} className="text-center text-medium-emphasis py-4">
                      {t('table.empty')}
                    </CTableDataCell>
                  </CTableRow>
                )}
                {currentApiKeys.map((apiKey, index) => {
                  // `active` defaults to true on the backend schema; treat a
                  // missing value as active so older rows still render right.
                  const isActive = apiKey.active !== false
                  return (
                    <CTableRow key={apiKey.apiKey}>
                      <CTableHeaderCell scope="row">
                        {(page - 1) * ITEMS_PER_PAGE + index + 1}
                      </CTableHeaderCell>
                      <CTableDataCell>
                        <code>{apiKey.apiKey}</code>
                      </CTableDataCell>
                      <CTableDataCell>
                        <div className="text-truncate" style={{ maxWidth: '150px' }}>
                          {apiKey.client}
                        </div>
                      </CTableDataCell>
                      <CTableDataCell>
                        <div className="text-truncate" style={{ maxWidth: '150px' }}>
                          {apiKey.description}
                        </div>
                      </CTableDataCell>
                      <CTableDataCell>
                        {apiKey.created_at ? new Date(apiKey.created_at).toLocaleString() : '-'}
                      </CTableDataCell>
                      <CTableDataCell>
                        <CBadge color={isActive ? 'success' : 'secondary'}>
                          {isActive ? t('table.status.active') : t('table.status.revoked')}
                        </CBadge>
                      </CTableDataCell>
                      <CTableDataCell className="text-end">
                        <CButton
                          color="danger"
                          variant="outline"
                          size="sm"
                          disabled={!isActive}
                          title={t('table.revokeAction')}
                          aria-label={t('table.revokeAction')}
                          onClick={() => setRevokeTarget(apiKey)}
                        >
                          <CIcon icon={cilTrash} />
                        </CButton>
                      </CTableDataCell>
                    </CTableRow>
                  )
                })}
              </CTableBody>
            </CTable>

            {/* Pagination */}
            <CPagination className="mt-4">
              <CPaginationItem disabled={page === 1} onClick={() => handlePageChange(page - 1)}>
                {t('table.previous')}
              </CPaginationItem>
              {[...Array(totalPages)].map((_, index) => (
                <CPaginationItem
                  key={index + 1}
                  active={index + 1 === page}
                  onClick={() => handlePageChange(index + 1)}
                >
                  {index + 1}
                </CPaginationItem>
              ))}
              <CPaginationItem
                disabled={page === totalPages}
                onClick={() => handlePageChange(page + 1)}
              >
                {t('table.next')}
              </CPaginationItem>
            </CPagination>
          </CCardBody>
        </CCard>
      </CCol>

      {revokeTarget && (
        <ConfirmDialog
          visible={!!revokeTarget}
          title={tm('apikeys.revoke.title')}
          message={tm('apikeys.revoke.message', { prefix: revokeTarget.apiKey })}
          confirmLabel={tm('apikeys.revoke.confirm')}
          confirmColor="danger"
          busy={revoking}
          onConfirm={handleConfirmRevoke}
          onCancel={() => setRevokeTarget(null)}
        />
      )}
    </CRow>
  )
}

ApiKeyTable.propTypes = {
  apiKeys: propTypes.array.isRequired,
  onRevoked: propTypes.func,
}

export default ApiKeyTable
