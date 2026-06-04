import React, { useState, useEffect, useCallback } from 'react'
import { CAlert } from '@coreui/react'
import ApikeysCreation from './ApikeysCreation'
import ApiKeyTable from './ApikeyTable'
import { getApiKeys } from '../../../api'
import { extractError } from '../../../utils/errors'
import { SkeletonTable } from '../../../components/Skeleton'

const ApiKey = () => {
  const [apiKeys, setApiKeys] = useState([])
  // Sprint 9: track first-load vs. refresh so the table renders a
  // skeleton on mount instead of "nothing → pop". Refreshes after a key
  // creation keep the existing rows visible while the request is in
  // flight (no flicker).
  const [isInitialLoading, setIsInitialLoading] = useState(true)
  const [error, setError] = useState(null)

  const refreshApiKeys = useCallback(() => {
    setError(null)
    return getApiKeys()
      .then((response) => {
        setApiKeys(response || [])
      })
      .catch((err) => {
        setError(extractError(err, 'No se pudieron cargar las API keys.'))
      })
      .finally(() => {
        setIsInitialLoading(false)
      })
  }, [])

  useEffect(() => {
    refreshApiKeys()
  }, [refreshApiKeys])

  return (
    <>
      <ApikeysCreation refreshApiKeys={refreshApiKeys} />
      {error && <CAlert color="danger">{error}</CAlert>}
      {isInitialLoading ? (
        <SkeletonTable columns={5} rows={5} hasActions />
      ) : (
        <ApiKeyTable apiKeys={apiKeys} onRevoked={refreshApiKeys} />
      )}
    </>
  )
}

export default ApiKey
