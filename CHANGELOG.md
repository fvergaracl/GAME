## Unreleased

### Feat

- update load test configuration to use service name for Postgres connection; improve comments for clarity
- update API key creation response details and improve documentation for authentication and configuration; refine user prompts in getting started guide
- update Keycloak realm and client ID in configuration files; refactor calculate_points method signature in BaseStrategy; remove outdated documentation files
- update author email
- add comprehensive documentation updates including new Code of Conduct, security policy, and improved setup instructions
- enhance _namespace_annotations function for better compatibility across Python versions
- update favicon.ico for improved branding
- add pre-commit hooks for local linting and update documentation
- add new image assets for game documentation and examples
- implement batched retrieval of user points by task IDs to optimize database queries
- add task points and query services
- enhance Sentry configuration for privacy and GDPR compliance; add data retention policy documentation
- **tests**: add comprehensive tests for API interceptors and keycloak integration

## v1.3.000 (2026-06-09)

### Feat

- add citation guidelines for GAME in README; enhance documentation for research use
- reset per-game state on game switch in GameTasksView; add tests for state management
- implement task parameters patching with full sync capabilities; enhance task management UI and localization
- implement timezone-aware UTC timestamps for created_at and updated_at fields in BaseModel
- add portal prop to CDropdown in GameTasksView, GamesManagementView, and StrategyLibraryView for improved dropdown behavior
- add date parsing and model-specific filtering to DashboardRepository; enhance pagination handling in FindBase
- enhance error handling in fetcher to mirror axios error shape and add tests for coverage
- add error handling for corrupt strategy loading and implement data-loss guards
- add regression tests for StrategyEditor load/hydration functionality
- implement CRUD management module with unsaved changes guard and comprehensive tests
- add Users explorer view with search functionality and wallet details
- enhance API key management with status indicators and revoke functionality
- implement per-game task management with CRUD operations
- Implement Game deletion and duplication modals with task count preview
- Add Games management view and CRUD functionality with internationalization support
- Implement reusable ConfirmDialog component for consistent confirmation modals
- Create ParamsEditor component for managing key/value parameters in forms
- Add useIsAdmin hook for centralized admin role checks across components
- **i18n**: Integrate management translations for English and Spanish
- Enhance app.json with management-related titles and labels
- Add management.json for English translations related to management features
- Add management.json for Spanish translations related to management features
- refactor dashboard widgets to use a single reusable KPI component; enhance loading and error handling
- add i18n support for sidebar navigation labels
- enhance configuration management and Docker setup; add validation for required secrets in protected environments
- add Dependabot and pip-audit workflows for automated dependency management and security auditing
- add PointsSimulationMixin for non-persisting user points simulation
- implement background worker for DSL execution-log persistence and analytics caching to enhance performance
- neutralize load_dotenv in test_cors_origins_default_to_empty_when_env_unset to ensure secure default behavior
- integrate toast notifications in StrategyAssignmentsView, StrategyEditor, and StrategyLibraryView
- add Strategy Observability View and related backend tests
- Enhance error handling and loading states with ErrorBoundary and Skeleton components
- Add ErrorBoundary and Skeleton components for improved error handling and loading states
- Implement glossary feature with onboarding tour and context
- integrate i18n support for app header and API keys management
- Update authorization checks and enhance test assertions for user point retrieval
- Add setup script for first-time Docker installation and environment initialization
- Update authorization logic to restrict access for non-admin users based on external user ID
- Enhance user access control with authorization checks for user data retrieval
- Implement strategy usage modal and enhance game listing with pagination and search
- Implement inline simulation and enhance simulation features
- enhance localization with new fields and toolbox categories for strategy blocks
- implement Block Help view and enhance documentation routing for strategy blocks
- add "Mis estrategias" library view for better strategy management and discoverability
- add support for else-if and else branches in rules
- Enhance simulation panel with guided inputs for accumulated values and cumulative runs
- Enhance Keycloak integration with proactive token renewal and session management
- Update CORS settings in environment configuration for local development
- Enhance strategy simulation with localized messages and starter rule for new workspaces
- Update Keycloak client configuration for SPA and backend integration
- Integrate Keycloak for authentication and enhance user session management
- Add observability stack with Prometheus and Grafana integration
- Implement sampled persistence for DSL execution traces and add metrics for strategy execution
- Enhance DSL block registration with i18n support and tooltips
- add tests for custom strategy assignment and lifecycle management in game and task services
- add version history modal and strategy picker for admin users
- implement strategy template picker modal and enhance strategy editor
- Update Blockly dependency and enhance App component with routing and lazy loading
- Implement DSL strategy execution and integration in UserPointsService
- Add StrategyDefinitionService for managing custom strategies
- **exports**: add admin UI for downloads and export history (Sprint 2)
- add export functionality with audit logging
- add support for trusted proxy IPs and enhance logging
- Add protocol mapper for game backend audience in realm template
- Add pluggable API key cache backends with Redis and in-memory options
- Implement rate limiting with pluggable backends using Redis and database
- Implement strategy registry and auto-discovery for strategy modules
- Enhance game access control and repository methods
- Implement database name resolution for production and staging environments
- Implement secure API key generation with hashing and prefixing
- Add complete entity-relationship diagram for GAME schema
- Add asynchronous handling for awaitable values and enhance token response normalization
- Implement database migration on startup and add logging for migration status
- Enhance QuickApiDashboard with new features for managing saved requests and request history
- Refactor App component and add QuickApiDashboard with API interaction features
- Enhance database configuration with connection pooling settings and logging options
- Add E2E API key support and enhance environment variable handling in scripts
- Add scripts for running E2E, unit, and load tests with improved options and error handling
- add unit tests for GameService to validate game creation, deletion, and retrieval logic
- enhance UserPointsService tests with additional scenarios and error handling
- add unit tests for UserService to validate point assignment and conversion logic
- add externalUserId handling in preview_convert and implement unit tests for WalletService
- refactor add_log function parameters and add unit tests for logging functionality
- add unit tests for UserPointsService with positive points handling and error cases
- enhance configuration and database handling in development and production scripts fix: improve role checking logic in JWT token validation chore: update dependencies and add ruff for linting

### Fix

- **exports**: wire user-interactions to UserActions and persist created_at
- Enhance restore_config_module to handle DB_NAME environment variable
- Update dependency-injector and fastapi versions in requirements.txt
- Update Node.js version in Dockerfile for build and development stages
- Correct strategy_service instantiation in TaskService and its tests
- Update Codecov upload step to use official action for improved reliability
- Ensure audience verification in JWT decoding and update tests accordingly
- Update user retrieval logic and make description field optional in API key schema
- Abuse prevention env vars and load test config
- Add retry logic to load test script and create method in base repository
- update GitHub Actions workflow for formatter with improved conditions and version upgrades
- update GAME logo image

### Refactor

- clean up comments and improve clarity in StrategyEditor
- remove Widgets, WidgetsBrand, and WidgetsDropdown components to streamline widget management
- Remove alembic migration logic from app startup and update dependencies in poetry.lock
- Simplify authentication logic by removing expired token handling and updating valid_access_token to use leeway

## v1.2.047 (2025-06-09)

### Fix

- handle exceptions when extracting POI IDs and improve wallet update logic

### Refactor

- **async**: convert update methods to async and enhance error handling in user points service

## v1.2.046 (2025-06-06)

### Refactor

- **async**: update service methods to use async/await for wallet operations
- **game**: enhance filtering options and improve code readability

## v1.2.044 (2025-05-29)

### Refactor

- **log**: improve log entry handling and add user creation on failure

## v1.2.043 (2025-05-29)

### Refactor

- **auth**: enhance token handling and add decoding without expiration check

## v1.2.042 (2025-05-28)

### Refactor

- **api**: improve code readability and enhance role checking logic in check_role function

## v1.2.041 (2025-05-28)

### Refactor

- **config**: remove unused ENV variable and enhance environment logging

## v1.2.040 (2025-05-26)

### Refactor

- **api**: update create_api_key endpoint to use async user retrieval and improve documentation
- **users**: remove debug print statements from add_action_to_user method for cleaner code
- **repository**: improve code readability by formatting query options and error handling
- **users**: enhance add_action_to_user method with additional logging for better traceability
- **users**: convert user action methods to async for improved performance
- **users**: convert add_log calls to async in convert_points_to_coins and add_action_to_user methods
- convert calculate_points and user retrieval methods to async

## v1.2.039 (2025-05-21)

### Fix

- **pyproject**: bump version to 1.2.039

### Refactor

- **userActionsService**: convert user_add_action_in_task to async and update related calls
- **taskService**: update methods to use async/await and improve code formatting

## v1.2.038 (2025-05-20)

### Feat

- **userPointsService**: enhance point assignment with case name support and refactor related schemas

### Fix

- **pyproject**: bump version to 1.2.038

## v1.2.037 (2025-05-20)

### Fix

- **pyproject**: bump version to 1.2.037

### Refactor

- **userService, games**: clean up code formatting and remove unnecessary print statements

## v1.2.036 (2025-05-13)

### Fix

- **userPointsService**: refactor point assignment logic and update version to 1.2.036

## v1.2.035 (2025-05-13)

### Feat

- **userPointsService**: add asynchronous method to assign points directly to a user and bump version to 1.2.035

## v1.2.034 (2025-04-07)

## v1.2.032 (2025-04-07)

## v1.2.031 (2025-04-02)

## v1.2.030 (2025-04-02)

## v1.2.029 (2025-04-02)

## v1.2.028 (2025-04-02)

## v1.2.027 (2025-04-02)

## v1.2.026 (2025-04-02)

## v1.2.025 (2025-04-02)

## v1.2.024 (2025-04-02)

## v1.2.023 (2025-04-02)

## v1.2.022 (2025-04-02)

## v1.2.021 (2025-04-02)

## v1.2.020 (2025-04-02)

## v1.2.019 (2025-04-02)

### Fix

- update time calculation to use UTC and bump version to 1.2.019

## v1.2.018 (2025-04-02)

### Refactor

- improve code readability and remove unnecessary error handling

## v1.2.017 (2025-03-13)

## v1.2.016 (2025-03-13)

## v1.2.015 (2025-03-04)

## v1.2.014 (2025-03-04)

## v1.2.013 (2025-03-04)

## v1.2.011 (2024-11-21)

### Feat

- fix problem with new users | chore: Add logs_repository to Container class and update .env file for integrated environment

## v1.2.010 (2024-11-07)

## v1.2.009 (2024-10-22)

## v1.2.008 (2024-10-22)

### Feat

- repositories related with KPIs added
- New models added related with KPIs
- greengage Strategy v1 developed
- apikey's endpoint added to test
- userpoints protected
- apikeys protected , game with apikey and Oauth2.0 protection
- enable apikey or OAuth2.0 as authentication
- update README with test coverage details
- Refactor test and added test of key generation in apikey.py and apikey_service.py
- test added , all utils
- two test added
- dashboard edited . Apikey integrated
- New troubleshooting element added
- Add ApiKey model and schema
- new strategy to award constant effort in a Collaborative Environment
- Add unit tests for base repository
- strategy schema modified
- Update game schema and models
- Modify of schema of base and game_params
- Changelog added

### Fix

- problem with dockerfile
- fix endpoint, update dockerfile
- upgrade some package in dockerfile
- test some issues
- action endpoint and some schemas
- deleted unwanted elements on some endpoints

## v0.0.005 (2024-02-08)

## v0.0.004 (2024-02-08)

## v0.0.003 (2024-02-08)

## v0.0.002 (2024-02-08)

## v0.0.001 (2024-02-07)

## v0.0.1 (2024-02-07)
