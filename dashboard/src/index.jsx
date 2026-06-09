import React from 'react'
import { createRoot } from 'react-dom/client'
import { Provider } from 'react-redux'
import 'core-js'

import App from './App'
import store from './store'
import keycloak from './keycloak'
// Side-effect import - initialises i18next before App
// renders so the first paint uses the resolved language.
import './i18n'

const renderApp = () => {
  createRoot(document.getElementById('root')).render(
    <Provider store={store}>
      <App />
    </Provider>,
  )
}

// ``check-sso`` restores an existing Keycloak session silently on every load
// (incl. after an F5) via the hidden iframe -> silent-check-sso.html, without
// forcing a redirect. The user still authenticates explicitly via the Log in
// button. After Keycloak redirects back with ``?code=...``, keycloak-js
// consumes it during this same init() call, so the post-login roundtrip is
// handled transparently.
keycloak
  .init({
    onLoad: 'check-sso',
    silentCheckSsoRedirectUri: `${window.location.origin}/silent-check-sso.html`,
    pkceMethod: 'S256',
    checkLoginIframe: false,
  })
  .then((authenticated) => {
    if (authenticated) {
      // Proactively renew the access token before it expires (Keycloak's
      // default lifespan is 5 min) so the session never drops on views that
      // make no API calls. updateToken() is a no-op until the token is within
      // ``minValidity`` seconds of expiry.
      keycloak.onTokenExpired = () => {
        keycloak.updateToken(30).catch(() => keycloak.login())
      }
      setInterval(() => {
        keycloak.updateToken(60).catch(() => {})
      }, 60_000)
    }
  })
  .catch((err) => {
    // Boot must not block if Keycloak is unreachable - public routes still
    // work; admin actions will surface a 401 from the backend.
    console.error('Keycloak init failed:', err)
  })
  .finally(renderApp)
