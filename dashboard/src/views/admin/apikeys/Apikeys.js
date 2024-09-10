import React, { useState, useEffect } from 'react'
import ApikeysCreation from './ApikeysCreation'
import ApiKeyTable from './ApikeyTable'
import { getApiKeys } from '../../../api'

const ApiKey = () => {
  const [apiKeys, setApiKeys] = useState([])

  useEffect(() => {
    refreshApiKeys()
  }, [])

  const refreshApiKeys = () => {
    getApiKeys().then((response) => {
      setApiKeys(response)
    })
  }

  return (
    <>
      <ApikeysCreation refreshApiKeys={refreshApiKeys} />
      <ApiKeyTable apiKeys={apiKeys} />
    </>
  )
}

export default ApiKey
