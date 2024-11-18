# Dashboard GAME

This project is a dashboard for a game. It is a web application that allows the user to manage the game. The user can create, read, update and delete players, games, and scores. The user can also see the ranking of the players.

## Features

- Create, read, update, and delete players
- Create, read, update, and delete games
- Create, read, update, and delete scores
- See the ranking of the players

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
