// Single source of truth for the admin check.
//
// Before this hook the ``AdministratorGAME`` role lookup was copy-pasted in
// at least three places, each subtly different:
//   * AppSidebar.jsx read resource_access[<API_CLIENT_ID>].roles, falling
//     back to the public SPA client id.
//   * StrategyLibraryView.jsx / StrategyEditor.jsx hard-coded the
//     resource_access.account.roles bucket.
// Those disagree whenever the role lands under a client id other than the
// one a given file happened to look at. ``useIsAdmin`` resolves the role
// regardless of which bucket Keycloak put it in: it checks the configured
// API client, the public SPA client, the legacy ``account`` bucket, *and*
// realm roles, then scans every remaining resource_access client as a last
// resort.
//
// This is a UX-only gate (hide admin-only affordances). The backend still
// enforces ``require_admin`` on every privileged endpoint, so a token that
// slips past this check just gets a 403 from the API.

import keycloak from '../keycloak'

export const ADMIN_ROLE = 'AdministratorGAME'

// Decode a JWT payload without verifying the signature. Only used as a
// fallback when keycloak-js hasn't populated ``tokenParsed`` yet (e.g. a
// component that renders before the adapter finishes init). Never throws.
const decodeToken = (token) => {
  try {
    const payload = token.split('.')[1]
    // base64url → base64 so atob accepts it.
    const normalized = payload.replace(/-/g, '+').replace(/_/g, '/')
    return JSON.parse(atob(normalized))
  } catch {
    return null
  }
}

const collectRoles = (parsed) => {
  if (!parsed) return []
  const roles = []
  const apiClientId =
    import.meta.env.VITE_KEYCLOAK_API_CLIENT_ID || import.meta.env.VITE_KEYCLOAK_CLIENT_ID
  const resourceAccess = parsed.resource_access || {}

  // Preferred buckets first, then sweep everything else so a role under an
  // unexpected client id still counts.
  const preferred = [apiClientId, import.meta.env.VITE_KEYCLOAK_CLIENT_ID, 'account']
  for (const clientId of preferred) {
    if (clientId && resourceAccess[clientId]?.roles) {
      roles.push(...resourceAccess[clientId].roles)
    }
  }
  for (const [clientId, entry] of Object.entries(resourceAccess)) {
    if (!preferred.includes(clientId) && Array.isArray(entry?.roles)) {
      roles.push(...entry.roles)
    }
  }
  if (Array.isArray(parsed.realm_access?.roles)) {
    roles.push(...parsed.realm_access.roles)
  }
  return roles
}

// Pure resolver - exported so non-React code (and tests) can reuse it
// without a hook. Returns a boolean.
export const resolveIsAdmin = (kc = keycloak) => {
  const parsed = kc?.tokenParsed || (kc?.token ? decodeToken(kc.token) : null)
  return collectRoles(parsed).includes(ADMIN_ROLE)
}

// React hook. ``keycloak`` is a module singleton (not React state), so
// there's nothing reactive to memoise on - the decode is a cheap synchronous
// read of the current token, recomputed each render to always reflect the
// live session. Components that gate the admin nav re-render on auth changes
// anyway (see AppSidebar's effect on ``keycloak.authenticated``).
export const useIsAdmin = () => resolveIsAdmin()

export default useIsAdmin
