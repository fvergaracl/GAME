import React from 'react'
import { createRoot } from 'react-dom/client'
import { Provider } from 'react-redux'
import 'core-js'

import App from './App'
import store from './store'
import keycloak from './keycloak'
// Sprint 10: side-effect import — initialises i18next before App
// renders so the first paint uses the resolved language.
import './i18n'

const renderApp = () => {
  createRoot(document.getElementById('root')).render(
    <Provider store={store}>
      <App />
    </Provider>,
  )
}

// No ``onLoad``: don't auto-redirect or run a silent SSO iframe on every
// page load. The user authenticates explicitly via the Log in button in the
// header. After Keycloak redirects back with ``?code=...``, keycloak-js
// detects and consumes it during this same init() call, so the post-login
// roundtrip is still handled transparently.
keycloak
  .init({
    pkceMethod: 'S256',
    checkLoginIframe: false,
  })
  .catch((err) => {
    // Boot must not block if Keycloak is unreachable — public routes still
    // work; admin actions will surface a 401 from the backend.
    console.error('Keycloak init failed:', err)
  })
  .finally(renderApp)
