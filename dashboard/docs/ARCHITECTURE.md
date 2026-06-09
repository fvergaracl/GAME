# Dashboard Architecture

> **Audience:** developers working on the GAME admin dashboard. For *what* the
> dashboard does from a user's point of view, see the
> [dashboard README](../README.md). For the backend it talks to, see the
> [GAME docs site](../../docs/source/index.rst).

The dashboard is the web admin for the GAME engine: an administrator uses it to
configure games, tasks, and strategies, issue API keys, export data, and
inspect per-user points and wallets. It is a single-page React application that
talks to the GAME REST API and authenticates against the same Keycloak realm as
the backend.

---

## Stack at a glance

| Concern            | Choice                                                            |
| ------------------ | ---------------------------------------------------------------- |
| Framework          | React 18 (function components + hooks)                           |
| Build tool         | Vite (`npm start` dev server, `npm run build` production)        |
| UI kit             | CoreUI React (`@coreui/react`) + CoreUI icons                    |
| Routing            | `react-router-dom` v6 (`BrowserRouter`, lazy routes)            |
| Global state       | Redux (`react-redux`) - UI/theme only; server data is per-view   |
| HTTP               | Axios, centralized in [`src/api.js`](../src/api.js)             |
| Auth               | Keycloak (`keycloak-js`), OIDC + PKCE                            |
| i18n               | `i18next` + `react-i18next`, **Spanish-first**, full English     |
| Strategy editor    | Blockly (lazy-loaded - ~1.5 MB, only when the editor opens)      |
| Charts             | Chart.js via `@coreui/react-chartjs`                            |
| Tests              | Vitest + Testing Library (`npm test`)                            |

---

## Boot sequence

The entry point is [`src/index.jsx`](../src/index.jsx). Boot is **auth-first**
so the first paint already reflects the session:

1. `i18n` is imported for its side effect, initializing `i18next` before render
   so the first paint uses the resolved language.
2. `keycloak.init({ onLoad: 'check-sso', pkceMethod: 'S256', … })` silently
   restores an existing session via a hidden `silent-check-sso.html` iframe -
   **no forced redirect**. After an explicit login, Keycloak redirects back
   with `?code=…`, which `keycloak-js` consumes during this same `init()` call.
3. On success, a token-refresh loop is installed: `onTokenExpired` and a 60 s
   interval call `updateToken()` so the session never drops on idle views
   (Keycloak's default access-token lifespan is 5 min).
4. **Boot never blocks on Keycloak.** If Keycloak is unreachable, `init()`
   rejects, the error is logged, and the app still renders - public routes work
   and admin actions surface a `401` from the backend.
5. `renderApp()` mounts `<Provider store={store}><App /></Provider>` regardless,
   via `.finally()`.

```
index.jsx
  ├─ import './i18n'            (side effect: init i18next)
  ├─ keycloak.init(check-sso)   (silent SSO restore, PKCE)
  │     └─ on auth → token auto-refresh loop
  └─ renderApp()  →  <Provider store><App /></Provider>
```

---

## Application shell & routing

[`src/App.jsx`](../src/App.jsx) is intentionally tiny and resilient:

```
<BrowserRouter>
  <ErrorBoundary section="App">        ← catches chunk-load failures (deploy mid-session)
    <Suspense fallback={<SkeletonCard/>}>
      /quick-api  → QuickApiDashboard   ← standalone, kept for an existing ops bookmark
      *           → DefaultLayout        ← CoreUI shell (sidebar + header + content)
```

Why this shape:

- **Lazy everything.** `DefaultLayout` and every view are `React.lazy()`-loaded
  so the initial bundle stays small. The Blockly-heavy `StrategyEditor` is its
  own chunk, downloaded only when an admin opens the editor.
- **An outer `ErrorBoundary`.** A chunk-load failure (e.g. a deploy mid-session
  invalidates a hashed chunk) used to crash the whole tree; now it's caught and
  the user is offered a reload while the URL stays navigable.

Routes are declared in [`src/routes.js`](../src/routes.js) and rendered by the
content area under `DefaultLayout`. Each entry is `{ path, name, element }`
with a lazy `element`. The route table:

| Path                              | View                        | Purpose                            |
| --------------------------------- | --------------------------- | ---------------------------------- |
| `/dashboard`                      | `Dashboard`                 | KPI summary                        |
| `/admin/games`                    | `GamesManagementView`       | Games CRUD                         |
| `/admin/games/:gameId/tasks`      | `GameTasksView`             | Per-game task CRUD                 |
| `/admin/users`                    | `UsersExplorerView`         | Read-only user points/wallet       |
| `/admin/api-keys`                 | `Apikeys`                   | API key create/revoke              |
| `/admin/exports`, `/…/history`    | `ExportData`, `ExportHistory` | Data exports                     |
| `/strategies/library`             | `StrategyLibraryView`       | Custom strategy discovery          |
| `/strategies/editor[/:id]`        | `StrategyEditor`            | Blockly DSL editor (heavy chunk)   |
| `/strategies/blocks-help/:slug`   | `BlockHelpView`             | Per-block help (opened from editor)|
| `/admin/strategies/assignments`   | `StrategyAssignmentsView`   | Which game/task uses which strategy|
| `/strategies/observability`       | `StrategyObservabilityView` | Execution metrics                  |
| `/strategies/compare`             | `StrategyComparisonView`    | A/B comparison                     |

---

## The HTTP layer

All backend access goes through [`src/api.js`](../src/api.js). It exports a
single configured Axios instance and thin `getRequest`/`postRequest`/
`patchRequest`/`putRequest`/`deleteRequest` helpers plus per-entity functions
(`getGame`, `listGameTasks`, …). Two things happen automatically:

- **Base URL** comes from `VITE_GAME_API_URL` (default
  `http://localhost:8000/api/v1`). ⚠️ It must **not** have a trailing slash;
  fetcher URLs are normalized in `src/utils/api.js` to avoid `404`s when the env
  value and the path both contribute a slash.
- **Bearer injection + silent refresh.** A request interceptor, when Keycloak is
  authenticated, calls `keycloak.updateToken(30)` (refresh if the token expires
  within 30 s) and sets `Authorization: Bearer <token>`. If the refresh fails
  (SSO session expired), it bounces the user to `keycloak.login()` and cancels
  the request.

Errors are normalized for display by `src/utils/errors.js` (`extractError`),
which views render inline. A backend "Network Error" with no status usually
means a masked `500` (the backend wraps errors so CORS headers survive) - check
the API logs, per the backend
[observability guide](../../docs/source/observability.rst).

---

## State model

There are **two** kinds of state, deliberately kept apart:

1. **Global (Redux, [`src/store.js`](../src/store.js))** - UI/theme concerns
   only (sidebar show/fold, color mode). It is *not* a server cache.
2. **Per-view local state (`useState`/`useEffect`)** - each view owns the data
   it fetches and re-fetches. Lists reload after each mutation via a
   `refreshTick` counter pattern (bump a number → an effect keyed on it
   re-fetches). This keeps each screen self-contained and predictable.

---

## Authentication & authorization

- The dashboard and backend share a Keycloak realm. Configure the client via
  `VITE_KEYCLOAK_URL`, `VITE_KEYCLOAK_REALM`, `VITE_KEYCLOAK_CLIENT_ID`
  (see [`src/keycloak.js`](../src/keycloak.js)).
- The admin panel **requires the `AdministratorGAME` realm role** - the same
  role the backend treats as admin (see the backend
  [authentication guide](../../docs/source/authentication.rst)). Without it, the
  backend rejects privileged actions (e.g. API-key creation) with `403`.
- The dashboard authenticates as a **user (bearer token)**, not via an API key.

---

## Internationalization

`i18next` is initialized in [`src/i18n/`](../src/i18n/) and split into
namespaces (e.g. `management`). Copy lives in
`src/i18n/locales/{es,en}/<namespace>.json`, **Spanish-first** with complete
English. Views pull their namespace with `useTranslation('management')` and
reference keys via `t('…')` - never hard-code user-facing strings.

---

## The management module (CRUD pattern)

The `/admin/*` CRUD surfaces are built from shared building blocks so every
entity behaves consistently. Reusable pieces in `src/components/`:

| Component         | Role                                                                |
| ----------------- | ------------------------------------------------------------------- |
| `ConfirmDialog`   | Accessibility-wired confirm modal for destructive/irreversible acts |
| `ParamsEditor`    | Repeatable `{key, value}` grid used by game/task forms              |
| `useUnsavedGuard` | The "discard unsaved changes?" guard wired into every form modal    |
| `Skeleton*`       | Loading placeholders (`SkeletonTable`, `SkeletonCard`)             |
| `useToast`        | Success confirmations; mutations surface errors inline + toast      |

Conventions every management view follows:

- HTTP helpers live in `src/api.js`; errors render inline via `extractError`.
- Mutations confirm success with a toast and **reload the list** afterwards.
- Copy is in the `management` i18n namespace.
- Tests sit beside the code as `*.test.{js,jsx}` and run with `npm test`.

### Worked example: `GameTasksView`

[`GameTasksView.jsx`](../src/views/admin/games/GameTasksView.jsx) (route
`/admin/games/:gameId/tasks`) is the canonical management view and a good map of
the pattern:

- **Keyed on the internal `gameId`** from the URL (`useParams`), so task
  mutations target rows by their internal UUID - what the backend expects.
- **Best-effort header label.** It calls `getGame(gameId)` only to show the
  human `externalGameId`; a failure there is non-blocking and falls back to the
  raw id, because the task list itself doesn't depend on it.
- **Reload via `refreshTick`.** Mirrors `GamesManagementView`. Tasks aren't
  server-paginated here (`listGameTasks` returns the whole set), so search is a
  light **client-side** filter over `externalTaskId`.
- **Per-game state reset (subtle, important).** Navigating between games only
  changes the `:gameId` route param - the component stays mounted. An effect
  keyed on `[gameId]` clears tasks, search, error, and every open modal. Without
  it, the previous game's rows or an open modal would survive the switch and act
  on a task belonging to the *old* game under the *new* `gameId`, which the
  backend correctly rejects as a cross-game `404`.
- **Dedicated modals** for each action: `TaskFormModal` (create/edit),
  `TaskBulkModal` (bulk create), `TaskDuplicateModal`, `TaskDeleteDialog` - each
  closing through the unsaved-changes guard where it edits.
- **Status as a badge.** Free-string task status is mapped to a color
  (`open`→success, `closed`→secondary, anything else→neutral) so unexpected
  values stay visible rather than disappearing.

This combination - internal-id keying, best-effort labels, `refreshTick`
reloads, explicit per-route-param reset, inline errors, and i18n copy - is the
template to copy when adding a new management surface.

---

## Local development

```bash
npm install
npm start          # Vite dev server with hot reload (http://localhost:3000)
npm run build      # production build → build/
npm test           # Vitest unit/component tests
npm run lint       # ESLint over src/**/*.{js,jsx}
```

Required environment (Vite reads `VITE_`-prefixed vars):

| Variable                   | Purpose                                             |
| -------------------------- | --------------------------------------------------- |
| `VITE_GAME_API_URL`        | Backend base URL (no trailing slash).               |
| `VITE_KEYCLOAK_URL`        | Keycloak base URL.                                  |
| `VITE_KEYCLOAK_REALM`      | Keycloak realm (same as the backend).               |
| `VITE_KEYCLOAK_CLIENT_ID`  | Public OIDC client id for the dashboard.            |

---

## Directory map

```
src/
├── api.js              # Axios instance + interceptor + per-entity HTTP helpers
├── keycloak.js         # Keycloak client config (from VITE_ env)
├── index.jsx           # boot: i18n → keycloak.init → render
├── App.jsx             # BrowserRouter + ErrorBoundary + Suspense + lazy routes
├── routes.js           # route table (lazy elements)
├── store.js            # Redux store (UI/theme state)
├── components/         # shared building blocks (ConfirmDialog, ParamsEditor, …)
├── hooks/              # custom hooks (useUnsavedGuard, useToast, …)
├── i18n/               # i18next init + locales/{es,en}/*.json
├── layout/             # DefaultLayout (CoreUI shell)
├── utils/              # api URL normalization, error extraction, …
└── views/
    ├── admin/          # CRUD management (games, tasks, users, apikeys)
    ├── strategies/     # Blockly editor, library, observability, comparison
    ├── exports/        # data export + history
    ├── dashboard/      # KPI dashboard
    └── quick-api/      # standalone Quick API tool
```
