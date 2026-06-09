# Dashboard GAME

The web admin for the GAME gamification engine. From here an administrator
configures the engine (games, tasks and their strategies), issues API keys for
integrating apps, exports data, and inspects per-user points and wallets.

> 🏗️ **New to the codebase?** Read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
> — boot sequence, routing, the HTTP/auth layer, state model, i18n, and the
> management-module CRUD pattern (with `GameTasksView` as a worked example).

## Features

- **Games** — create, edit, duplicate (deep copy incl. tasks/params) and delete games.
- **Tasks** — per-game task lifecycle: create (single or bulk), edit, duplicate and delete.
- **Strategies** — author DSL strategies in the Blockly editor, publish/version them, and assign them to games/tasks.
- **API keys** — create and revoke integration keys.
- **Users** — read-only explorer for a user's points (by game/task) and wallet balance/transactions.
- **Exports & observability** — download datasets and review strategy execution metrics.

## Management module

The CRUD management surface lives under `/admin/*` and is built from a few
shared building blocks so every entity behaves consistently:

| Surface | Route | Capabilities |
|---|---|---|
| Games | `/admin/games` | list (server search/paginate) · create · edit · duplicate · delete |
| Tasks | `/admin/games/:gameId/tasks` | list · create · bulk-create · edit · duplicate · delete |
| API keys | `/admin/api-keys` | list · create · revoke |
| Users | `/admin/users` | look up points + wallet (read-only) |

Shared pieces (in `src/components/`): `ConfirmDialog` (a11y-wired confirm modal
for destructive/irreversible actions), `ParamsEditor` (repeatable `{key,value}`
grid used by the game/task forms), and `useUnsavedGuard` (the "discard unsaved
changes?" guard wired into every form modal's close path). All entity HTTP
helpers live in `src/api.js`; user-facing copy is in the `management` i18n
namespace (`src/i18n/locales/{es,en}/management.json`), Spanish-first with full
English.

Mutating actions surface backend errors inline via `extractError` and confirm
success with a toast (`useToast`); lists reload after each save. Tests for the
module live alongside the code (`*.test.{js,jsx}`) and run with `npm test`.

## Administration panel

Is mandatory create a Rol in Keycloak with the name **"AdministratorGAME"** to access the administration panel. The user must have this Rol to access the administration panel to manage the game, and see all the features such as create API Keys

### Installation

```bash
$ npm install
```

or

```bash
$ yarn install
```

### Basic usage

```bash
# dev server with hot reload at http://localhost:3000
$ npm start
```

or

```bash
# dev server with hot reload at http://localhost:3000
$ yarn start
```

Navigate to [http://localhost:3000](http://localhost:3000). The app will automatically reload if you change any of the source files.

#### Build

Run `build` to build the project. The build artifacts will be stored in the `build/` directory.

```bash
# build for production with minification
$ npm run build
```

or

```bash
# build for production with minification
$ yarn build
```

## What's included

Within the download you'll find the following directories and files, logically grouping common assets and providing both compiled and minified variations. You'll see something like this:

```
coreui-free-react-admin-template
├── public/          # static files
│   ├── favicon.ico
│   └── manifest.json
│
├── src/             # project root
│   ├── assets/      # images, icons, etc.
│   ├── components/  # common components - header, footer, sidebar, etc.
│   ├── layouts/     # layout containers
│   ├── scss/        # scss styles
│   ├── views/       # application views
│   ├── _nav.js      # sidebar navigation config
│   ├── App.js
│   ├── index.js
│   ├── routes.js    # routes config
│   └── store.js     # template state example
│
├── index.html       # html template
├── ...
├── package.json
├── ...
└── vite.config.mjs  # vite config
```

## Credits to Creators

### Łukasz Holeczek

- Twitter: [@lukaszholeczek](https://twitter.com/lukaszholeczek)
- GitHub: [mrholek](https://github.com/mrholek)

### Andrzej Kopański

- GitHub: [xidedix](https://github.com/xidedix)

### CoreUI Team

- Twitter: [@core_ui](https://twitter.com/core_ui)
- GitHub Organization: [CoreUI](https://github.com/coreui)
- CoreUI Members: [GitHub People](https://github.com/orgs/coreui/people)
