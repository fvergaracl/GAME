import React, { useEffect, useMemo, useState } from 'react'
import {
  CAlert,
  CBadge,
  CButton,
  CCard,
  CCardBody,
  CCardHeader,
  CCol,
  CContainer,
  CFormCheck,
  CFormInput,
  CFormLabel,
  CFormSelect,
  CFormTextarea,
  CInputGroup,
  CInputGroupText,
  CListGroup,
  CListGroupItem,
  CRow,
  CSpinner,
} from '@coreui/react'
import { buildCurlCommand, mergeUrl, pushHistoryEntry, safeParseJson, upsertSavedRequest } from './quickApiUtils.mjs'
import './QuickApiDashboard.scss'

const STORAGE_KEY = 'game_quick_api_dashboard'
const SAVED_REQUESTS_STORAGE_KEY = 'game_quick_api_dashboard_saved_requests'
const HISTORY_STORAGE_KEY = 'game_quick_api_dashboard_history'

const DEFAULT_BASE_URL = import.meta.env.VITE_GAME_API_URL || 'http://localhost:8000/api/v1'
const MAX_HISTORY = 10

const QUICK_ACTIONS = [
  { name: 'Health Check', method: 'GET', path: '/kpi/health_check', body: '' },
  { name: 'List Strategies', method: 'GET', path: '/strategies', body: '' },
  { name: 'Dashboard Summary', method: 'GET', path: '/dashboard/summary?group_by=day', body: '' },
  { name: 'List API Keys', method: 'GET', path: '/apikey', body: '' },
  {
    name: 'Create API Key',
    method: 'POST',
    path: '/apikey/create',
    body: JSON.stringify(
      {
        client: 'dashboard-client',
        description: 'Quick API dashboard generated key',
      },
      null,
      2,
    ),
  },
]

const METHOD_COLORS = {
  GET: 'info',
  POST: 'success',
  PUT: 'warning',
  PATCH: 'warning',
  DELETE: 'danger',
}

const getMethodColor = (method) => METHOD_COLORS[(method || '').toUpperCase()] || 'secondary'

const getStatusColor = (status) => {
  if (typeof status !== 'number') {
    return 'danger'
  }

  if (status >= 200 && status < 300) {
    return 'success'
  }

  if (status >= 400 && status < 500) {
    return 'warning'
  }

  if (status >= 500) {
    return 'danger'
  }

  return 'secondary'
}

const parseMaybeJson = async (response) => {
  const raw = await response.text()

  if (!raw) {
    return { parsed: null, raw: '' }
  }

  try {
    return { parsed: JSON.parse(raw), raw }
  } catch (_error) {
    return { parsed: null, raw }
  }
}

const QuickApiDashboard = () => {
  const [baseUrl, setBaseUrl] = useState(DEFAULT_BASE_URL)
  const [bearerToken, setBearerToken] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [method, setMethod] = useState('GET')
  const [path, setPath] = useState('/kpi/health_check')
  const [body, setBody] = useState('')
  const [responseMeta, setResponseMeta] = useState(null)
  const [responseBody, setResponseBody] = useState('')
  const [responseRawBody, setResponseRawBody] = useState('')
  const [responseView, setResponseView] = useState('pretty')
  const [requestError, setRequestError] = useState('')
  const [infoMessage, setInfoMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [saveName, setSaveName] = useState('')
  const [savedRequests, setSavedRequests] = useState([])
  const [requestHistory, setRequestHistory] = useState([])
  const [showSensitive, setShowSensitive] = useState(false)
  const [savedFilter, setSavedFilter] = useState('')
  const [historyFilter, setHistoryFilter] = useState('')

  const setErrorMessage = (message) => {
    setInfoMessage('')
    setRequestError(message)
  }

  const setSuccessMessage = (message) => {
    setRequestError('')
    setInfoMessage(message)
  }

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored)
        setBaseUrl(parsed.baseUrl || DEFAULT_BASE_URL)
        setBearerToken(parsed.bearerToken || '')
        setApiKey(parsed.apiKey || '')
        setMethod(parsed.method || 'GET')
        setPath(parsed.path || '/kpi/health_check')
        setBody(parsed.body || '')
      }
    } catch (_error) {
      localStorage.removeItem(STORAGE_KEY)
    }

    try {
      const storedSavedRequests = localStorage.getItem(SAVED_REQUESTS_STORAGE_KEY)
      if (storedSavedRequests) {
        const parsedSavedRequests = JSON.parse(storedSavedRequests)
        if (Array.isArray(parsedSavedRequests)) {
          setSavedRequests(parsedSavedRequests)
        }
      }
    } catch (_error) {
      localStorage.removeItem(SAVED_REQUESTS_STORAGE_KEY)
    }

    try {
      const storedHistory = localStorage.getItem(HISTORY_STORAGE_KEY)
      if (storedHistory) {
        const parsedHistory = JSON.parse(storedHistory)
        if (Array.isArray(parsedHistory)) {
          setRequestHistory(parsedHistory.slice(0, MAX_HISTORY))
        }
      }
    } catch (_error) {
      localStorage.removeItem(HISTORY_STORAGE_KEY)
    }
  }, [])

  useEffect(() => {
    const payload = { baseUrl, bearerToken, apiKey, method, path, body }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(payload))
  }, [apiKey, baseUrl, bearerToken, body, method, path])

  useEffect(() => {
    localStorage.setItem(SAVED_REQUESTS_STORAGE_KEY, JSON.stringify(savedRequests))
  }, [savedRequests])

  useEffect(() => {
    localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(requestHistory))
  }, [requestHistory])

  const canSendBody = useMemo(() => ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method), [method])

  const currentUrl = useMemo(() => mergeUrl(baseUrl, path), [baseUrl, path])

  const filteredSavedRequests = useMemo(() => {
    const filter = savedFilter.trim().toLowerCase()
    if (!filter) {
      return savedRequests
    }

    return savedRequests.filter((savedRequest) => {
      const searchable = `${savedRequest.name || ''} ${savedRequest.method || ''} ${savedRequest.path || ''}`
      return searchable.toLowerCase().includes(filter)
    })
  }, [savedFilter, savedRequests])

  const filteredRequestHistory = useMemo(() => {
    const filter = historyFilter.trim().toLowerCase()
    if (!filter) {
      return requestHistory
    }

    return requestHistory.filter((historyEntry) => {
      const searchable = `${historyEntry.method || ''} ${historyEntry.path || ''} ${historyEntry.status || ''}`
      return searchable.toLowerCase().includes(filter)
    })
  }, [historyFilter, requestHistory])

  const canSwitchResponseView = Boolean(responseRawBody) && responseRawBody !== responseBody
  const displayedResponseBody = responseView === 'raw' ? responseRawBody : responseBody

  const copyToClipboard = async (value, successMessage, errorMessage) => {
    if (!value) {
      setErrorMessage(errorMessage)
      return
    }

    try {
      await navigator.clipboard.writeText(value)
      setSuccessMessage(successMessage)
    } catch (_error) {
      setErrorMessage(errorMessage)
    }
  }

  const sendRequest = async (override = null) => {
    const currentMethod = (override?.method || method).toUpperCase()
    const currentPath = override?.path || path
    const currentBody = override?.body ?? body
    const url = mergeUrl(baseUrl, currentPath)

    if (!url) {
      setErrorMessage('Base URL and path are empty.')
      return
    }

    const headers = {
      Accept: 'application/json',
    }

    if (bearerToken.trim()) {
      headers.Authorization = `Bearer ${bearerToken.trim()}`
    }

    if (apiKey.trim()) {
      headers['X-API-Key'] = apiKey.trim()
    }

    const options = { method: currentMethod, headers }

    if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(currentMethod) && currentBody.trim()) {
      const parsedBody = safeParseJson(currentBody)
      if (!parsedBody.ok) {
        setErrorMessage(parsedBody.error)
        return
      }

      options.body = parsedBody.compact
      headers['Content-Type'] = 'application/json'
    }

    setIsLoading(true)
    setRequestError('')
    setInfoMessage('')
    setResponseMeta(null)
    setResponseBody('')
    setResponseRawBody('')

    const start = performance.now()

    try {
      const response = await fetch(url, options)
      const elapsedMs = Math.round(performance.now() - start)
      const parsed = await parseMaybeJson(response)
      const executedAt = new Date().toISOString()

      const rawText = parsed.raw || '(empty response body)'
      const prettyText = parsed.parsed !== null ? JSON.stringify(parsed.parsed, null, 2) : rawText

      setResponseMeta({
        url,
        method: currentMethod,
        status: response.status,
        ok: response.ok,
        elapsedMs,
        contentType: response.headers.get('content-type') || '(not provided)',
        bodySize: parsed.raw ? new Blob([parsed.raw]).size : 0,
      })
      setResponseBody(prettyText)
      setResponseRawBody(rawText)
      setResponseView(parsed.parsed !== null ? 'pretty' : 'raw')

      setRequestHistory((previousHistory) =>
        pushHistoryEntry(
          previousHistory,
          {
            id: `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
            method: currentMethod,
            path: currentPath,
            body: currentBody,
            url,
            status: response.status,
            ok: response.ok,
            elapsedMs,
            executedAt,
          },
          MAX_HISTORY,
        ),
      )
    } catch (error) {
      const elapsedMs = Math.round(performance.now() - start)
      setErrorMessage(error?.message || 'Request failed')
      setRequestHistory((previousHistory) =>
        pushHistoryEntry(
          previousHistory,
          {
            id: `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
            method: currentMethod,
            path: currentPath,
            body: currentBody,
            url,
            status: 'NETWORK_ERROR',
            ok: false,
            elapsedMs,
            executedAt: new Date().toISOString(),
          },
          MAX_HISTORY,
        ),
      )
    } finally {
      setIsLoading(false)
    }
  }

  const runQuickAction = async (action) => {
    setMethod(action.method)
    setPath(action.path)
    setBody(action.body)
    await sendRequest(action)
  }

  const handleFormatBody = () => {
    const parsed = safeParseJson(body)
    if (!parsed.ok) {
      setErrorMessage(parsed.error)
      return
    }

    setBody(parsed.formatted)
    setSuccessMessage('Body formatted as pretty JSON.')
  }

  const handleCopyCurl = async () => {
    const curlCommand = buildCurlCommand({
      url: currentUrl,
      method,
      bearerToken,
      apiKey,
      body,
    })

    if (!curlCommand.ok) {
      setErrorMessage(curlCommand.error)
      return
    }

    await copyToClipboard(
      curlCommand.command,
      'cURL command copied to clipboard.',
      'Unable to copy cURL command to clipboard.',
    )
  }

  const handleCopyResponse = async () => {
    await copyToClipboard(
      displayedResponseBody,
      'Response body copied to clipboard.',
      'There is no response body to copy.',
    )
  }

  const handleCopyUrl = async () => {
    await copyToClipboard(currentUrl, 'URL copied to clipboard.', 'There is no URL to copy.')
  }

  const handleClearResponse = () => {
    setResponseMeta(null)
    setResponseBody('')
    setResponseRawBody('')
    setRequestError('')
    setInfoMessage('')
  }

  const handleSaveCurrentRequest = () => {
    const trimmedName = saveName.trim()
    if (!trimmedName) {
      setErrorMessage('Write a name before saving the request.')
      return
    }

    setSavedRequests((previousSavedRequests) =>
      upsertSavedRequest(previousSavedRequests, {
        name: trimmedName,
        method,
        path,
        body,
      }),
    )

    setSuccessMessage(`Saved request "${trimmedName}".`)
    setSaveName('')
  }

  const handleLoadSavedRequest = (savedRequest) => {
    setMethod(savedRequest.method)
    setPath(savedRequest.path)
    setBody(savedRequest.body || '')
    setSuccessMessage(`Loaded request "${savedRequest.name}".`)
  }

  const handleDeleteSavedRequest = (savedRequestName) => {
    setSavedRequests((previousSavedRequests) =>
      previousSavedRequests.filter((savedRequest) => savedRequest.name !== savedRequestName),
    )
    setSuccessMessage(`Deleted request "${savedRequestName}".`)
  }

  const handleRunSavedRequest = async (savedRequest) => {
    setMethod(savedRequest.method)
    setPath(savedRequest.path)
    setBody(savedRequest.body || '')
    await sendRequest(savedRequest)
  }

  const handleReplayHistoryEntry = async (historyEntry) => {
    setMethod(historyEntry.method)
    setPath(historyEntry.path)
    setBody(historyEntry.body || '')
    await sendRequest(historyEntry)
  }

  const clearAllSavedRequests = () => {
    setSavedRequests([])
    setSuccessMessage('All saved requests were removed.')
  }

  const clearHistory = () => {
    setRequestHistory([])
    setSuccessMessage('History cleared.')
  }

  return (
    <CContainer className="quick-api-dashboard py-4">
      <CRow className="g-4">
        <CCol xs={12}>
          <CCard>
            <CCardHeader className="d-flex justify-content-between align-items-center">
              <strong>GAME Quick API Dashboard</strong>
              <CBadge color="info">Fast consume mode</CBadge>
            </CCardHeader>
            <CCardBody>
              <div className="quick-api-url-preview mb-3">
                <div className="d-flex flex-wrap justify-content-between align-items-center gap-2">
                  <div className="d-flex flex-wrap align-items-center gap-2">
                    <CBadge color={getMethodColor(method)}>{method}</CBadge>
                    <code className="quick-api-endpoint-code">{currentUrl || '(complete Base URL + Path)'}</code>
                  </div>
                  <CButton
                    size="sm"
                    color="dark"
                    variant="outline"
                    onClick={handleCopyUrl}
                    disabled={!currentUrl || isLoading}
                  >
                    Copy URL
                  </CButton>
                </div>
              </div>

              <CRow className="g-3">
                <CCol md={8}>
                  <CFormLabel htmlFor="api-base-url">Base URL</CFormLabel>
                  <CFormInput
                    id="api-base-url"
                    value={baseUrl}
                    onChange={(event) => setBaseUrl(event.target.value)}
                    placeholder="http://localhost:8000/api/v1"
                  />
                </CCol>
                <CCol md={4}>
                  <CFormLabel htmlFor="http-method">Method</CFormLabel>
                  <CFormSelect
                    id="http-method"
                    value={method}
                    onChange={(event) => setMethod(event.target.value)}
                    options={['GET', 'POST', 'PUT', 'PATCH', 'DELETE']}
                  />
                </CCol>
                <CCol xs={12}>
                  <CFormCheck
                    id="show-sensitive"
                    type="switch"
                    label="Show credentials"
                    checked={showSensitive}
                    onChange={(event) => setShowSensitive(event.target.checked)}
                  />
                </CCol>
                <CCol md={6}>
                  <CFormLabel htmlFor="bearer-token">Bearer token (optional)</CFormLabel>
                  <CFormInput
                    id="bearer-token"
                    type={showSensitive ? 'text' : 'password'}
                    value={bearerToken}
                    onChange={(event) => setBearerToken(event.target.value)}
                    placeholder="eyJhbGciOi..."
                  />
                </CCol>
                <CCol md={6}>
                  <CFormLabel htmlFor="api-key">X-API-Key (optional)</CFormLabel>
                  <CFormInput
                    id="api-key"
                    type={showSensitive ? 'text' : 'password'}
                    value={apiKey}
                    onChange={(event) => setApiKey(event.target.value)}
                    placeholder="gk_..."
                  />
                </CCol>
                <CCol xs={12}>
                  <CFormLabel htmlFor="path">Path</CFormLabel>
                  <CInputGroup>
                    <CInputGroupText>Path</CInputGroupText>
                    <CFormInput
                      id="path"
                      value={path}
                      onChange={(event) => setPath(event.target.value)}
                      placeholder="/dashboard/summary?group_by=day"
                    />
                  </CInputGroup>
                </CCol>
                {canSendBody && (
                  <CCol xs={12}>
                    <CFormLabel htmlFor="json-body">JSON body</CFormLabel>
                    <CFormTextarea
                      id="json-body"
                      rows={8}
                      value={body}
                      onChange={(event) => setBody(event.target.value)}
                      placeholder='{"key":"value"}'
                      className="quick-api-mono"
                    />
                  </CCol>
                )}
              </CRow>

              <div className="d-flex gap-2 flex-wrap mt-4">
                <CButton color="primary" onClick={() => sendRequest()} disabled={isLoading}>
                  {isLoading ? (
                    <>
                      <CSpinner size="sm" className="me-2" /> Sending...
                    </>
                  ) : (
                    'Send Request'
                  )}
                </CButton>
                <CButton color="dark" variant="outline" onClick={handleCopyCurl} disabled={isLoading}>
                  Copy cURL
                </CButton>
                <CButton
                  color="dark"
                  variant="outline"
                  onClick={handleFormatBody}
                  disabled={isLoading || !canSendBody || !body.trim()}
                >
                  Format JSON
                </CButton>
                {QUICK_ACTIONS.map((action) => (
                  <CButton
                    key={action.name}
                    color="secondary"
                    variant="outline"
                    onClick={() => runQuickAction(action)}
                    disabled={isLoading}
                  >
                    {action.name}
                  </CButton>
                ))}
              </div>

              <CRow className="g-2 mt-3">
                <CCol md={8}>
                  <CFormLabel htmlFor="save-name">Save current request as</CFormLabel>
                  <CFormInput
                    id="save-name"
                    value={saveName}
                    onChange={(event) => setSaveName(event.target.value)}
                    placeholder="Health check no auth"
                  />
                </CCol>
                <CCol md={4} className="d-flex align-items-end">
                  <CButton color="success" className="w-100" onClick={handleSaveCurrentRequest}>
                    Save request
                  </CButton>
                </CCol>
              </CRow>

              {infoMessage && (
                <CAlert color="success" className="mt-3 mb-0">
                  {infoMessage}
                </CAlert>
              )}
            </CCardBody>
          </CCard>
        </CCol>

        <CCol xl={6}>
          <CCard className="h-100">
            <CCardHeader className="d-flex justify-content-between align-items-center gap-2">
              <span>
                Saved Requests <CBadge color="secondary">{savedRequests.length}</CBadge>
              </span>
              <CButton
                size="sm"
                color="danger"
                variant="outline"
                onClick={clearAllSavedRequests}
                disabled={savedRequests.length === 0}
              >
                Clear all
              </CButton>
            </CCardHeader>
            <CCardBody>
              <CFormInput
                value={savedFilter}
                onChange={(event) => setSavedFilter(event.target.value)}
                placeholder="Filter by name, method or path"
                className="mb-3"
              />
              {filteredSavedRequests.length === 0 && (
                <CAlert color="secondary" className="mb-0">
                  No saved requests match this filter.
                </CAlert>
              )}
              {filteredSavedRequests.length > 0 && (
                <CListGroup className="quick-api-scroll-list">
                  {filteredSavedRequests.map((savedRequest, index) => (
                    <CListGroupItem key={savedRequest.name || `saved_request_${index}`}>
                      <div className="d-flex flex-wrap justify-content-between gap-2">
                        <div>
                          <div className="d-flex align-items-center gap-2">
                            <strong>{savedRequest.name}</strong>
                            <CBadge color={getMethodColor(savedRequest.method)}>{savedRequest.method}</CBadge>
                          </div>
                          <code className="quick-api-item-code">{savedRequest.path}</code>
                        </div>
                        <div className="d-flex gap-2">
                          <CButton
                            size="sm"
                            color="secondary"
                            variant="outline"
                            onClick={() => handleLoadSavedRequest(savedRequest)}
                          >
                            Load
                          </CButton>
                          <CButton
                            size="sm"
                            color="primary"
                            variant="outline"
                            onClick={() => handleRunSavedRequest(savedRequest)}
                            disabled={isLoading}
                          >
                            Run
                          </CButton>
                          <CButton
                            size="sm"
                            color="danger"
                            variant="outline"
                            onClick={() => handleDeleteSavedRequest(savedRequest.name)}
                          >
                            Delete
                          </CButton>
                        </div>
                      </div>
                    </CListGroupItem>
                  ))}
                </CListGroup>
              )}
            </CCardBody>
          </CCard>
        </CCol>

        <CCol xl={6}>
          <CCard className="h-100">
            <CCardHeader className="d-flex justify-content-between align-items-center gap-2">
              <span>
                Recent History <CBadge color="secondary">{requestHistory.length}</CBadge>
              </span>
              <CButton
                size="sm"
                color="danger"
                variant="outline"
                onClick={clearHistory}
                disabled={requestHistory.length === 0}
              >
                Clear history
              </CButton>
            </CCardHeader>
            <CCardBody>
              <CFormInput
                value={historyFilter}
                onChange={(event) => setHistoryFilter(event.target.value)}
                placeholder="Filter by method, path or status"
                className="mb-3"
              />
              {filteredRequestHistory.length === 0 && (
                <CAlert color="secondary" className="mb-0">
                  No history entries match this filter.
                </CAlert>
              )}
              {filteredRequestHistory.length > 0 && (
                <CListGroup className="quick-api-scroll-list">
                  {filteredRequestHistory.map((historyEntry, index) => (
                    <CListGroupItem key={historyEntry.id || `history_entry_${index}`}>
                      <div className="d-flex flex-wrap justify-content-between gap-2">
                        <div>
                          <div className="d-flex flex-wrap align-items-center gap-2">
                            <CBadge color={getMethodColor(historyEntry.method)}>{historyEntry.method}</CBadge>
                            <CBadge color={getStatusColor(historyEntry.status)}>{historyEntry.status}</CBadge>
                            <code className="quick-api-item-code">{historyEntry.path}</code>
                          </div>
                          <div className="text-body-secondary small mt-1">
                            {historyEntry.elapsedMs}ms |{' '}
                            {historyEntry.executedAt
                              ? new Date(historyEntry.executedAt).toLocaleString()
                              : 'unknown timestamp'}
                          </div>
                        </div>
                        <CButton
                          size="sm"
                          color="primary"
                          variant="outline"
                          onClick={() => handleReplayHistoryEntry(historyEntry)}
                          disabled={isLoading}
                        >
                          Replay
                        </CButton>
                      </div>
                    </CListGroupItem>
                  ))}
                </CListGroup>
              )}
            </CCardBody>
          </CCard>
        </CCol>

        <CCol xs={12}>
          <CCard>
            <CCardHeader className="d-flex justify-content-between align-items-center gap-2">
              <span>Response</span>
              <div className="d-flex gap-2 flex-wrap">
                {canSwitchResponseView && (
                  <>
                    <CButton
                      size="sm"
                      color={responseView === 'pretty' ? 'primary' : 'dark'}
                      variant={responseView === 'pretty' ? undefined : 'outline'}
                      onClick={() => setResponseView('pretty')}
                    >
                      Pretty
                    </CButton>
                    <CButton
                      size="sm"
                      color={responseView === 'raw' ? 'primary' : 'dark'}
                      variant={responseView === 'raw' ? undefined : 'outline'}
                      onClick={() => setResponseView('raw')}
                    >
                      Raw
                    </CButton>
                  </>
                )}
                <CButton
                  size="sm"
                  color="dark"
                  variant="outline"
                  onClick={handleCopyResponse}
                  disabled={!displayedResponseBody}
                >
                  Copy response
                </CButton>
                <CButton size="sm" color="dark" variant="outline" onClick={handleClearResponse}>
                  Clear response
                </CButton>
              </div>
            </CCardHeader>
            <CCardBody>
              {requestError && <CAlert color="danger">{requestError}</CAlert>}
              {responseMeta && (
                <CAlert color={responseMeta.ok ? 'success' : 'warning'}>
                  <div>
                    <strong>{responseMeta.method}</strong> {responseMeta.url}
                  </div>
                  <div className="d-flex flex-wrap gap-2 mt-2">
                    <CBadge color={getStatusColor(responseMeta.status)}>Status {responseMeta.status}</CBadge>
                    <CBadge color="info">Time {responseMeta.elapsedMs}ms</CBadge>
                    <CBadge color="secondary">{responseMeta.contentType}</CBadge>
                    <CBadge color="dark">Size {responseMeta.bodySize} bytes</CBadge>
                  </div>
                </CAlert>
              )}
              <pre className="quick-api-response-body">{displayedResponseBody || 'No response yet.'}</pre>
            </CCardBody>
          </CCard>
        </CCol>
      </CRow>
    </CContainer>
  )
}

export default QuickApiDashboard
