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
  CFormInput,
  CFormLabel,
  CFormSelect,
  CFormTextarea,
  CRow,
  CSpinner,
} from '@coreui/react'

const STORAGE_KEY = 'game_quick_api_dashboard'

const DEFAULT_BASE_URL = import.meta.env.VITE_GAME_API_URL || 'http://localhost:8000/api/v1'

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

const mergeUrl = (baseUrl, path) => {
  const normalizedBase = (baseUrl || '').trim().replace(/\/+$/, '')
  const normalizedPath = (path || '').trim()

  if (!normalizedPath) {
    return normalizedBase
  }

  if (/^https?:\/\//i.test(normalizedPath)) {
    return normalizedPath
  }

  if (!normalizedBase) {
    return normalizedPath
  }

  return `${normalizedBase}/${normalizedPath.replace(/^\/+/, '')}`
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
  const [requestError, setRequestError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (!stored) {
        return
      }
      const parsed = JSON.parse(stored)

      setBaseUrl(parsed.baseUrl || DEFAULT_BASE_URL)
      setBearerToken(parsed.bearerToken || '')
      setApiKey(parsed.apiKey || '')
      setMethod(parsed.method || 'GET')
      setPath(parsed.path || '/kpi/health_check')
      setBody(parsed.body || '')
    } catch (_error) {
      localStorage.removeItem(STORAGE_KEY)
    }
  }, [])

  useEffect(() => {
    const payload = { baseUrl, bearerToken, apiKey, method, path, body }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(payload))
  }, [apiKey, baseUrl, bearerToken, body, method, path])

  const canSendBody = useMemo(() => ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method), [method])

  const sendRequest = async (override = null) => {
    const currentMethod = override?.method || method
    const currentPath = override?.path || path
    const currentBody = override?.body ?? body
    const url = mergeUrl(baseUrl, currentPath)

    if (!url) {
      setRequestError('Base URL and path are empty.')
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
      try {
        const jsonBody = JSON.parse(currentBody)
        options.body = JSON.stringify(jsonBody)
        headers['Content-Type'] = 'application/json'
      } catch (_error) {
        setRequestError('Invalid JSON body.')
        return
      }
    }

    setIsLoading(true)
    setRequestError('')
    setResponseMeta(null)
    setResponseBody('')

    const start = performance.now()

    try {
      const response = await fetch(url, options)
      const elapsedMs = Math.round(performance.now() - start)
      const parsed = await parseMaybeJson(response)

      setResponseMeta({
        url,
        method: currentMethod,
        status: response.status,
        ok: response.ok,
        elapsedMs,
      })

      if (parsed.parsed !== null) {
        setResponseBody(JSON.stringify(parsed.parsed, null, 2))
      } else if (parsed.raw) {
        setResponseBody(parsed.raw)
      } else {
        setResponseBody('(empty response body)')
      }
    } catch (error) {
      setRequestError(error?.message || 'Request failed')
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

  return (
    <CContainer className="py-4">
      <CRow className="g-4">
        <CCol xs={12}>
          <CCard>
            <CCardHeader className="d-flex justify-content-between align-items-center">
              <strong>GAME Quick API Dashboard</strong>
              <CBadge color="info">Fast consume mode</CBadge>
            </CCardHeader>
            <CCardBody>
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
                <CCol md={6}>
                  <CFormLabel htmlFor="bearer-token">Bearer token (optional)</CFormLabel>
                  <CFormInput
                    id="bearer-token"
                    value={bearerToken}
                    onChange={(event) => setBearerToken(event.target.value)}
                    placeholder="eyJhbGciOi..."
                  />
                </CCol>
                <CCol md={6}>
                  <CFormLabel htmlFor="api-key">X-API-Key (optional)</CFormLabel>
                  <CFormInput
                    id="api-key"
                    value={apiKey}
                    onChange={(event) => setApiKey(event.target.value)}
                    placeholder="gk_..."
                  />
                </CCol>
                <CCol xs={12}>
                  <CFormLabel htmlFor="path">Path</CFormLabel>
                  <CFormInput
                    id="path"
                    value={path}
                    onChange={(event) => setPath(event.target.value)}
                    placeholder="/dashboard/summary?group_by=day"
                  />
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
            </CCardBody>
          </CCard>
        </CCol>

        <CCol xs={12}>
          <CCard>
            <CCardHeader>Response</CCardHeader>
            <CCardBody>
              {requestError && <CAlert color="danger">{requestError}</CAlert>}
              {responseMeta && (
                <CAlert color={responseMeta.ok ? 'success' : 'warning'}>
                  <strong>{responseMeta.method}</strong> {responseMeta.url}
                  <br />
                  Status: <strong>{responseMeta.status}</strong> | Time:{' '}
                  <strong>{responseMeta.elapsedMs}ms</strong>
                </CAlert>
              )}
              <pre
                style={{
                  background: '#111827',
                  color: '#f8fafc',
                  padding: '1rem',
                  borderRadius: '0.5rem',
                  minHeight: '280px',
                  margin: 0,
                  overflow: 'auto',
                }}
              >
                {responseBody || 'No response yet.'}
              </pre>
            </CCardBody>
          </CCard>
        </CCol>
      </CRow>
    </CContainer>
  )
}

export default QuickApiDashboard
