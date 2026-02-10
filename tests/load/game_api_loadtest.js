import http from "k6/http";
import { check, fail, sleep } from "k6";
import { Counter, Rate, Trend } from "k6/metrics";

/*
Load test for GAME API

How to run (localhost example):
set -a; source .env; set +a
BASE_URL=http://localhost:8000/api/v1 \
k6 run tests/load/game_api_loadtest.js

If you already have an API key, you can pass it:
set -a; source .env; set +a
BASE_URL=http://localhost:8000/api/v1 \
X_API_KEY=$X_API_KEY \
k6 run tests/load/game_api_loadtest.js

If X_API_KEY is not provided, setup tries to create one via POST /apikey/create
using admin credentials resolved automatically from env:
- ACCESS_TOKEN (preferred, if already available)
- otherwise KEYCLOAK_TOKEN_URL or KEYCLOAK_URL+KEYCLOAK_REALM
- KEYCLOAK_CLIENT_ID / KEYCLOAK_CLIENT_SECRET
- KEYCLOAK_ADMIN_USERNAME (or KEYCLOAK_USER_WITH_ROLE_USERNAME)
- KEYCLOAK_USER_WITH_ROLE_PASSWORD
*/

const BASE_URL = stripTrailingSlash(__ENV.BASE_URL || "http://localhost:8000/api/v1");
const LOAD_MODE = (__ENV.LOAD_MODE || "100").toLowerCase();
const DEFAULT_TARGET_VUS = LOAD_MODE === "1000" ? 1000 : 100;
const TARGET_VUS = intEnv("TARGET_VUS", DEFAULT_TARGET_VUS);

const WARMUP_DURATION = __ENV.WARMUP_DURATION || "30s";
const HOLD_DURATION = __ENV.HOLD_DURATION || "2m";
const RAMP_DOWN_DURATION = __ENV.RAMP_DOWN_DURATION || "30s";
const REQUEST_TIMEOUT = __ENV.REQUEST_TIMEOUT || "30s";
const USER_POOL_SIZE = intEnv("USER_POOL_SIZE", 200);

const MIX_A = floatEnv("MIX_A", 70);
const MIX_B = floatEnv("MIX_B", 25);
const MIX_C = floatEnv("MIX_C", 5);

const MAX_ATTEMPTS = intEnv("MAX_ATTEMPTS", 3);
const BACKOFF_MS = intEnv("BACKOFF_MS", 120);
const BACKOFF_FACTOR = floatEnv("BACKOFF_FACTOR", 2);
const RETRYABLE_STATUS_CODES = parseStatusCodes(
  __ENV.RETRYABLE_STATUS_CODES || "408,429,502,503,504"
);

const ERROR_RATE_THRESHOLD = floatEnv(
  "ERROR_RATE_THRESHOLD",
  TARGET_VUS >= 1000 ? 0.03 : 0.01
);
const P95_TARGET_MS = intEnv("P95_TARGET_MS", 800);
const ENFORCE_P95 =
  (__ENV.ENFORCE_P95 || (TARGET_VUS <= 100 ? "1" : "0")) === "1";

const WRITE_AUTH_MODE = (__ENV.WRITE_AUTH_MODE || "bearer_preferred").toLowerCase();
const WRITE_RANDOM_IP = (__ENV.WRITE_RANDOM_IP || "1") === "1";

const allocation = allocateScenarioVUs(TARGET_VUS, MIX_A, MIX_B, MIX_C);

const scenarioAStatus2xx = new Counter("scenario_a_status_2xx");
const scenarioAStatus4xx = new Counter("scenario_a_status_4xx");
const scenarioAStatus5xx = new Counter("scenario_a_status_5xx");
const scenarioARequests = new Counter("scenario_a_requests_total");
const scenarioALatency = new Trend("scenario_a_req_duration_ms", true);
const scenarioASuccess = new Rate("scenario_a_success_rate");

const scenarioBStatus2xx = new Counter("scenario_b_status_2xx");
const scenarioBStatus4xx = new Counter("scenario_b_status_4xx");
const scenarioBStatus5xx = new Counter("scenario_b_status_5xx");
const scenarioBRequests = new Counter("scenario_b_requests_total");
const scenarioBLatency = new Trend("scenario_b_req_duration_ms", true);
const scenarioBSuccess = new Rate("scenario_b_success_rate");

const scenarioCStatus2xx = new Counter("scenario_c_status_2xx");
const scenarioCStatus4xx = new Counter("scenario_c_status_4xx");
const scenarioCStatus5xx = new Counter("scenario_c_status_5xx");
const scenarioCRequests = new Counter("scenario_c_requests_total");
const scenarioCLatency = new Trend("scenario_c_req_duration_ms", true);
const scenarioCSuccess = new Rate("scenario_c_success_rate");

const thresholds = {
  http_req_failed: [`rate<${ERROR_RATE_THRESHOLD}`],
};
if (ENFORCE_P95) {
  thresholds.http_req_duration = [`p(95)<${P95_TARGET_MS}`];
}

export const options = {
  summaryTrendStats: ["avg", "min", "med", "max", "p(50)", "p(90)", "p(95)", "p(99)"],
  thresholds: thresholds,
  scenarios: buildScenarios(allocation),
};

function buildScenarios(vusByScenario) {
  const scenarios = {};
  if (vusByScenario.a > 0) {
    scenarios.scenario_a_read_heavy = {
      executor: "ramping-vus",
      exec: "scenarioAReadHeavy",
      startVUs: 0,
      stages: [
        { duration: WARMUP_DURATION, target: vusByScenario.a },
        { duration: HOLD_DURATION, target: vusByScenario.a },
        { duration: RAMP_DOWN_DURATION, target: 0 },
      ],
      gracefulRampDown: "15s",
      tags: { scenario_group: "A" },
    };
  }
  if (vusByScenario.b > 0) {
    scenarios.scenario_b_write_heavy = {
      executor: "ramping-vus",
      exec: "scenarioBWriteHeavy",
      startVUs: 0,
      stages: [
        { duration: WARMUP_DURATION, target: vusByScenario.b },
        { duration: HOLD_DURATION, target: vusByScenario.b },
        { duration: RAMP_DOWN_DURATION, target: 0 },
      ],
      gracefulRampDown: "15s",
      tags: { scenario_group: "B" },
    };
  }
  if (vusByScenario.c > 0) {
    scenarios.scenario_c_aggregation_heavy = {
      executor: "ramping-vus",
      exec: "scenarioCAggregationHeavy",
      startVUs: 0,
      stages: [
        { duration: WARMUP_DURATION, target: vusByScenario.c },
        { duration: HOLD_DURATION, target: vusByScenario.c },
        { duration: RAMP_DOWN_DURATION, target: 0 },
      ],
      gracefulRampDown: "15s",
      tags: { scenario_group: "C" },
    };
  }
  return scenarios;
}

export function setup() {
  const runId = uniqueRunId();
  const accessToken = resolveAccessToken();

  let xApiKey = firstNonEmpty([
    __ENV.X_API_KEY,
    __ENV.EXISTING_API_KEY,
    __ENV.BOOTSTRAP_X_API_KEY,
  ]);
  xApiKey = xApiKey ? xApiKey.trim() : "";
  let createdApiKey = false;

  if (!xApiKey) {
    if (!accessToken) {
      fail(
        "No X_API_KEY provided and no ACCESS_TOKEN available to create one. " +
          "Set X_API_KEY or ACCESS_TOKEN."
      );
    }
    const apiKeyCreated = createApiKeyForRun(runId, accessToken);
    xApiKey = apiKeyCreated.apiKey;
    createdApiKey = true;
  }

  const gameAuthHeaders = authHeadersForGames({ xApiKey: xApiKey, accessToken: accessToken });
  if (Object.keys(gameAuthHeaders).length === 0) {
    fail("Unable to authenticate /games endpoints. Provide X_API_KEY or ACCESS_TOKEN.");
  }

  const externalGameId = `k6-game-${runId}`;
  const createGamePayload = {
    externalGameId: externalGameId,
    platform: __ENV.GAME_PLATFORM || "web",
    strategyId: __ENV.GAME_STRATEGY_ID || "default",
  };

  const createGameRes = requestWithRetry(
    "POST",
    `${BASE_URL}/games`,
    createGamePayload,
    {
      headers: mergeHeaders(gameAuthHeaders, {
        "Content-Type": "application/json",
      }),
      tags: { phase: "setup", endpoint: "create_game" },
      timeout: REQUEST_TIMEOUT,
    }
  );

  if (!is2xx(createGameRes)) {
    fail(
      `Setup failed creating game. status=${createGameRes.status} body=${safeBody(
        createGameRes
      )}`
    );
  }
  const gameBody = safeJson(createGameRes);
  const gameId = gameBody.gameId;
  if (!gameId) {
    fail(`Setup failed: missing gameId in create game response: ${safeBody(createGameRes)}`);
  }

  const taskExternalIds = [
    `k6-task-${runId}-1`,
    `k6-task-${runId}-2`,
  ];

  for (let i = 0; i < taskExternalIds.length; i++) {
    const createTaskPayload = {
      externalTaskId: taskExternalIds[i],
      strategyId: __ENV.TASK_STRATEGY_ID || "default",
    };
    const createTaskRes = requestWithRetry(
      "POST",
      `${BASE_URL}/games/${gameId}/tasks`,
      createTaskPayload,
      {
        headers: mergeHeaders(gameAuthHeaders, {
          "Content-Type": "application/json",
        }),
        tags: { phase: "setup", endpoint: "create_task" },
        timeout: REQUEST_TIMEOUT,
      }
    );
    if (!is2xx(createTaskRes)) {
      fail(
        `Setup failed creating task ${taskExternalIds[i]}. status=${createTaskRes.status} body=${safeBody(
          createTaskRes
        )}`
      );
    }
  }

  const userPool = [];
  for (let u = 0; u < USER_POOL_SIZE; u++) {
    userPool.push(`k6-user-${runId}-${pad(u, 4)}`);
  }

  return {
    runId: runId,
    accessToken: accessToken,
    xApiKey: xApiKey,
    createdApiKey: createdApiKey,
    gameId: gameId,
    externalGameId: externalGameId,
    taskExternalIds: taskExternalIds,
    userPool: userPool,
  };
}

export function scenarioAReadHeavy(data) {
  const strategiesNoAuth = requestWithRetry(
    "GET",
    `${BASE_URL}/strategies`,
    null,
    {
      headers: {},
      tags: { endpoint: "strategies_no_auth", scenario: "A" },
      timeout: REQUEST_TIMEOUT,
    }
  );
  recordScenarioMetrics("A", strategiesNoAuth);
  check(strategiesNoAuth, {
    "A /strategies no-auth is 200": (r) => r.status === 200,
  });

  const strategiesAuth = requestWithRetry(
    "GET",
    `${BASE_URL}/strategies`,
    null,
    {
      headers: authHeadersForStrategies(data),
      tags: { endpoint: "strategies_with_auth", scenario: "A" },
      timeout: REQUEST_TIMEOUT,
    }
  );
  recordScenarioMetrics("A", strategiesAuth);
  check(strategiesAuth, {
    "A /strategies with-auth is 200": (r) => r.status === 200,
  });

  const gamesRes = requestWithRetry(
    "GET",
    `${BASE_URL}/games?page=1&page_size=10`,
    null,
    {
      headers: authHeadersForGames(data),
      tags: { endpoint: "games_list", scenario: "A" },
      timeout: REQUEST_TIMEOUT,
    }
  );
  recordScenarioMetrics("A", gamesRes);
  check(gamesRes, {
    "A /games list is 200": (r) => r.status === 200,
  });

  sleep(0.05);
}

export function scenarioBWriteHeavy(data) {
  const taskIndex = (__ITER + __VU) % data.taskExternalIds.length;
  const taskExternalId = data.taskExternalIds[taskIndex];
  const userIndex = (__VU * 131 + __ITER * 17) % data.userPool.length;
  const externalUserId = data.userPool[userIndex];

  const writeHeaders = authHeadersForWrites(data, userIndex);

  const actionPayload = {
    typeAction: "TASK_COMPLETED",
    data: {
      source: "k6",
      runId: data.runId,
      vu: __VU,
      iter: __ITER,
    },
    description: "k6 action event",
    externalUserId: externalUserId,
  };

  const actionRes = requestWithRetry(
    "POST",
    `${BASE_URL}/games/${data.gameId}/tasks/${taskExternalId}/action`,
    actionPayload,
    {
      headers: mergeHeaders(writeHeaders, { "Content-Type": "application/json" }),
      tags: { endpoint: "task_action", scenario: "B" },
      timeout: REQUEST_TIMEOUT,
    }
  );
  recordScenarioMetrics("B", actionRes);
  check(actionRes, {
    "B task action returns 2xx": (r) => is2xx(r),
  });

  const pointsPayload = {
    externalUserId: externalUserId,
    data: {
      source: "k6",
      event: "task_completed",
      runId: data.runId,
      vu: __VU,
      iter: __ITER,
    },
    isSimulated: false,
  };

  const pointsRes = requestWithRetry(
    "POST",
    `${BASE_URL}/games/${data.gameId}/tasks/${taskExternalId}/points`,
    pointsPayload,
    {
      headers: mergeHeaders(writeHeaders, { "Content-Type": "application/json" }),
      tags: { endpoint: "task_points", scenario: "B" },
      timeout: REQUEST_TIMEOUT,
    }
  );
  recordScenarioMetrics("B", pointsRes);
  check(pointsRes, {
    "B task points returns 2xx": (r) => is2xx(r),
  });

  sleep(0.02);
}

export function scenarioCAggregationHeavy(data) {
  const headers = authHeadersForGames(data);

  const pointsDetailsRes = requestWithRetry(
    "GET",
    `${BASE_URL}/games/${data.gameId}/points/details`,
    null,
    {
      headers: headers,
      tags: { endpoint: "game_points_details", scenario: "C" },
      timeout: REQUEST_TIMEOUT,
    }
  );
  recordScenarioMetrics("C", pointsDetailsRes);
  check(pointsDetailsRes, {
    "C game points details is 200": (r) => r.status === 200,
  });

  const dashboardRes = requestWithRetry(
    "GET",
    `${BASE_URL}/dashboard/summary?group_by=day`,
    null,
    {
      headers: headers,
      tags: { endpoint: "dashboard_summary", scenario: "C" },
      timeout: REQUEST_TIMEOUT,
    }
  );
  recordScenarioMetrics("C", dashboardRes);
  check(dashboardRes, {
    "C dashboard summary is 200": (r) => r.status === 200,
  });

  sleep(0.05);
}

export function teardown(data) {
  if (!data || !data.gameId) {
    return;
  }

  const headers = authHeadersForGames(data);
  const deleteRes = requestWithRetry(
    "DELETE",
    `${BASE_URL}/games/${data.gameId}`,
    null,
    {
      headers: headers,
      tags: { phase: "teardown", endpoint: "delete_game" },
      timeout: REQUEST_TIMEOUT,
    }
  );

  if (!is2xx(deleteRes) && deleteRes.status !== 404) {
    console.error(
      `Teardown warning: failed deleting game ${data.gameId}. status=${deleteRes.status} body=${safeBody(
        deleteRes
      )}`
    );
  }

  if (data.createdApiKey) {
    // No public API-key revoke/delete endpoint exists in current API.
    // Key created in setup may remain active and should be rotated manually.
    console.warn(
      "Teardown limitation: API key created during setup could not be revoked via API " +
        "(no delete/revoke endpoint available)."
    );
  }
}

export function handleSummary(data) {
  const httpFailedRate = metric(data, "http_req_failed", "rate");
  const reqRate = metric(data, "http_reqs", "rate");
  const reqCount = metric(data, "http_reqs", "count");
  const p50 = metric(data, "http_req_duration", "p(50)");
  const p90 = metric(data, "http_req_duration", "p(90)");
  const p95 = metric(data, "http_req_duration", "p(95)");
  const p99 = metric(data, "http_req_duration", "p(99)");

  const lines = [];
  lines.push("=== GAME API k6 Load Summary ===");
  lines.push(`Base URL: ${BASE_URL}`);
  lines.push(`Mode: ${LOAD_MODE}, target VUs: ${TARGET_VUS}`);
  lines.push(
    `Mix A/B/C: ${MIX_A}% / ${MIX_B}% / ${MIX_C}% -> VUs ${allocation.a}/${allocation.b}/${allocation.c}`
  );
  lines.push(
    `Durations: warmup=${WARMUP_DURATION}, hold=${HOLD_DURATION}, rampDown=${RAMP_DOWN_DURATION}`
  );
  lines.push("");
  lines.push("Global metrics:");
  lines.push(`- http_req_failed: ${(httpFailedRate * 100).toFixed(2)}%`);
  lines.push(`- http_req_duration p50/p90/p95/p99 (ms): ${fmt(p50)} / ${fmt(p90)} / ${fmt(p95)} / ${fmt(p99)}`);
  lines.push(`- http_reqs count: ${Math.round(reqCount)}`);
  lines.push(`- RPS (http_reqs rate): ${fmt(reqRate)}`);
  lines.push("");
  lines.push("Status distribution by scenario (2xx/4xx/5xx):");
  lines.push(formatScenarioStatusLine(data, "A"));
  lines.push(formatScenarioStatusLine(data, "B"));
  lines.push(formatScenarioStatusLine(data, "C"));
  lines.push("");
  lines.push("Thresholds:");
  lines.push(`- http_req_failed < ${(ERROR_RATE_THRESHOLD * 100).toFixed(2)}%`);
  if (ENFORCE_P95) {
    lines.push(`- http_req_duration p(95) < ${P95_TARGET_MS} ms`);
  } else {
    lines.push("- http_req_duration p(95) threshold disabled for this run");
  }

  return {
    stdout: `${lines.join("\n")}\n`,
  };
}

function resolveAccessToken() {
  const fromEnv = firstNonEmpty([__ENV.ACCESS_TOKEN, __ENV.ADMIN_BEARER_TOKEN]);
  if (fromEnv) {
    return fromEnv.trim();
  }

  const tokenUrl = resolveTokenUrl();
  const username = firstNonEmpty([
    __ENV.ADMIN_USERNAME,
    __ENV.KEYCLOAK_ADMIN_USERNAME,
    __ENV.E2E_KEYCLOAK_ADMIN_USERNAME,
    __ENV.KEYCLOAK_USER_WITH_ROLE_USERNAME,
    "game_admin@example.com",
  ]);
  const password = firstNonEmpty([
    __ENV.ADMIN_PASSWORD,
    __ENV.KEYCLOAK_USER_WITH_ROLE_PASSWORD,
    __ENV.E2E_KEYCLOAK_ADMIN_PASSWORD,
  ]);
  const clientId = firstNonEmpty([
    __ENV.KEYCLOAK_CLIENT_ID,
    __ENV.CLIENT_ID,
    __ENV.E2E_KEYCLOAK_CLIENT_ID,
  ]);
  const clientSecret = firstNonEmpty([
    __ENV.KEYCLOAK_CLIENT_SECRET,
    __ENV.CLIENT_SECRET,
    __ENV.E2E_KEYCLOAK_CLIENT_SECRET,
  ]);

  if (!tokenUrl || !username || !password || !clientId) {
    return "";
  }

  const form = {
    grant_type: "password",
    username: username,
    password: password,
    client_id: clientId,
  };
  if (clientSecret) {
    form.client_secret = clientSecret;
  }

  const res = requestWithRetry("POST", tokenUrl, formEncode(form), {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    tags: { phase: "setup", endpoint: "token" },
    timeout: REQUEST_TIMEOUT,
  });

  if (!is2xx(res)) {
    fail(`Failed obtaining access token. status=${res.status} body=${safeBody(res)}`);
  }
  const body = safeJson(res);
  const token = body.access_token;
  if (!token) {
    fail(`Token response missing access_token: ${safeBody(res)}`);
  }
  return token;
}

function createApiKeyForRun(runId, accessToken) {
  const payload = {
    client: `k6-load-client-${runId}`,
    description: `k6 load test key for run ${runId}`,
  };
  const headers = {
    Authorization: `Bearer ${accessToken}`,
    "Content-Type": "application/json",
  };
  const bootstrap = firstNonEmpty([
    __ENV.BOOTSTRAP_X_API_KEY,
    __ENV.EXISTING_API_KEY,
    __ENV.X_API_KEY,
  ]);
  if (bootstrap) {
    headers["X-API-Key"] = bootstrap.trim();
  }

  const res = requestWithRetry("POST", `${BASE_URL}/apikey/create`, payload, {
    headers: headers,
    tags: { phase: "setup", endpoint: "create_apikey" },
    timeout: REQUEST_TIMEOUT,
  });

  if (res.status !== 201) {
    fail(
      `Failed creating API key in setup. status=${res.status} body=${safeBody(res)}`
    );
  }
  const body = safeJson(res);
  if (!body.apiKey) {
    fail(`API key creation response missing apiKey: ${safeBody(res)}`);
  }
  return body;
}

function requestWithRetry(method, url, body, params) {
  let attempt = 1;
  let response = null;

  while (attempt <= MAX_ATTEMPTS) {
    response = doHttpRequest(method, url, body, params);
    const shouldRetryNow = shouldRetryResponse(response);
    if (!shouldRetryNow || attempt === MAX_ATTEMPTS) {
      return response;
    }

    const backoffMs = BACKOFF_MS * Math.pow(BACKOFF_FACTOR, attempt - 1);
    sleep(backoffMs / 1000);
    attempt += 1;
  }
  return response;
}

function doHttpRequest(method, url, body, params) {
  const upper = method.toUpperCase();
  if (body === null || body === undefined) {
    return http.request(upper, url, null, params);
  }
  const hasJsonHeader =
    params &&
    params.headers &&
    (params.headers["Content-Type"] === "application/json" ||
      params.headers["content-type"] === "application/json");
  const payload = hasJsonHeader && typeof body !== "string" ? JSON.stringify(body) : body;
  return http.request(upper, url, payload, params);
}

function shouldRetryResponse(res) {
  if (!res) {
    return true;
  }
  if (res.status === 0) {
    return true;
  }
  return RETRYABLE_STATUS_CODES[res.status] === true;
}

function authHeadersForGames(data) {
  if (data.xApiKey) {
    return { "X-API-Key": data.xApiKey };
  }
  if (data.accessToken) {
    return { Authorization: `Bearer ${data.accessToken}` };
  }
  return {};
}

function authHeadersForStrategies(data) {
  return authHeadersForGames(data);
}

function authHeadersForWrites(data, userIndex) {
  const headers = {};
  if ((WRITE_AUTH_MODE === "bearer" || WRITE_AUTH_MODE === "bearer_preferred") && data.accessToken) {
    headers.Authorization = `Bearer ${data.accessToken}`;
  } else if (data.xApiKey) {
    headers["X-API-Key"] = data.xApiKey;
  } else if (data.accessToken) {
    headers.Authorization = `Bearer ${data.accessToken}`;
  }

  if (WRITE_RANDOM_IP) {
    const ip = syntheticIp(userIndex);
    headers["X-Forwarded-For"] = ip;
    headers["X-Real-IP"] = ip;
  }
  return headers;
}

function recordScenarioMetrics(scenario, res) {
  const status = res ? res.status : 0;
  const duration = res && res.timings ? res.timings.duration : 0;
  const success = status >= 200 && status < 300;

  if (scenario === "A") {
    scenarioARequests.add(1);
    scenarioALatency.add(duration);
    scenarioASuccess.add(success);
    addStatusClassCounters(status, scenarioAStatus2xx, scenarioAStatus4xx, scenarioAStatus5xx);
    return;
  }
  if (scenario === "B") {
    scenarioBRequests.add(1);
    scenarioBLatency.add(duration);
    scenarioBSuccess.add(success);
    addStatusClassCounters(status, scenarioBStatus2xx, scenarioBStatus4xx, scenarioBStatus5xx);
    return;
  }
  scenarioCRequests.add(1);
  scenarioCLatency.add(duration);
  scenarioCSuccess.add(success);
  addStatusClassCounters(status, scenarioCStatus2xx, scenarioCStatus4xx, scenarioCStatus5xx);
}

function addStatusClassCounters(status, c2xx, c4xx, c5xx) {
  if (status >= 200 && status < 300) {
    c2xx.add(1);
    return;
  }
  if (status >= 400 && status < 500) {
    c4xx.add(1);
    return;
  }
  c5xx.add(1);
}

function formatScenarioStatusLine(data, scenarioName) {
  let k2 = "";
  let k4 = "";
  let k5 = "";
  if (scenarioName === "A") {
    k2 = "scenario_a_status_2xx";
    k4 = "scenario_a_status_4xx";
    k5 = "scenario_a_status_5xx";
  } else if (scenarioName === "B") {
    k2 = "scenario_b_status_2xx";
    k4 = "scenario_b_status_4xx";
    k5 = "scenario_b_status_5xx";
  } else {
    k2 = "scenario_c_status_2xx";
    k4 = "scenario_c_status_4xx";
    k5 = "scenario_c_status_5xx";
  }

  const v2 = metric(data, k2, "count");
  const v4 = metric(data, k4, "count");
  const v5 = metric(data, k5, "count");
  const total = v2 + v4 + v5;
  return `- Scenario ${scenarioName}: 2xx=${Math.round(v2)} 4xx=${Math.round(v4)} 5xx=${Math.round(v5)} total=${Math.round(total)}`;
}

function metric(data, metricName, key) {
  if (!data || !data.metrics || !data.metrics[metricName] || !data.metrics[metricName].values) {
    return 0;
  }
  const values = data.metrics[metricName].values;
  return values[key] || 0;
}

function mergeHeaders(a, b) {
  const out = {};
  const first = a || {};
  const second = b || {};
  for (const k in first) {
    out[k] = first[k];
  }
  for (const k2 in second) {
    out[k2] = second[k2];
  }
  return out;
}

function parseStatusCodes(csv) {
  const map = {};
  const chunks = String(csv || "").split(",");
  for (let i = 0; i < chunks.length; i++) {
    const n = parseInt(chunks[i].trim(), 10);
    if (!isNaN(n)) {
      map[n] = true;
    }
  }
  return map;
}

function resolveTokenUrl() {
  const explicit = firstNonEmpty([__ENV.KEYCLOAK_TOKEN_URL, __ENV.AUTH_TOKEN_URL]);
  if (explicit) {
    return explicit.trim();
  }

  const keycloakUrl = firstNonEmpty([__ENV.KEYCLOAK_URL, __ENV.E2E_KEYCLOAK_URL]);
  const realm = firstNonEmpty([__ENV.KEYCLOAK_REALM, __ENV.E2E_KEYCLOAK_REALM]);
  if (!keycloakUrl || !realm) {
    return "";
  }
  return `${stripTrailingSlash(keycloakUrl)}/realms/${realm}/protocol/openid-connect/token`;
}

function firstNonEmpty(values) {
  if (!values || values.length === 0) {
    return "";
  }
  for (let i = 0; i < values.length; i++) {
    const value = values[i];
    if (value !== undefined && value !== null && String(value).trim() !== "") {
      return String(value);
    }
  }
  return "";
}

function intEnv(name, defaultValue) {
  const raw = __ENV[name];
  if (!raw) {
    return defaultValue;
  }
  const parsed = parseInt(raw, 10);
  if (isNaN(parsed) || parsed <= 0) {
    return defaultValue;
  }
  return parsed;
}

function floatEnv(name, defaultValue) {
  const raw = __ENV[name];
  if (!raw) {
    return defaultValue;
  }
  const parsed = parseFloat(raw);
  if (isNaN(parsed)) {
    return defaultValue;
  }
  return parsed;
}

function allocateScenarioVUs(total, rawA, rawB, rawC) {
  const a = rawA > 0 ? rawA : 0;
  const b = rawB > 0 ? rawB : 0;
  const c = rawC > 0 ? rawC : 0;
  const sum = a + b + c;
  const effectiveSum = sum > 0 ? sum : 100;
  const wa = sum > 0 ? a / effectiveSum : 0.7;
  const wb = sum > 0 ? b / effectiveSum : 0.25;
  let vusA = Math.floor(total * wa);
  let vusB = Math.floor(total * wb);
  let vusC = total - vusA - vusB;

  if (vusC < 0) {
    vusC = 0;
  }
  if (vusA === 0 && wa > 0 && total >= 1) {
    vusA = 1;
  }
  if (vusB === 0 && wb > 0 && total - vusA >= 1) {
    vusB = 1;
  }
  vusC = total - vusA - vusB;
  if (vusC < 0) {
    vusC = 0;
  }
  return { a: vusA, b: vusB, c: vusC };
}

function uniqueRunId() {
  return `${Date.now()}-${Math.floor(Math.random() * 1000000)}`;
}

function syntheticIp(seed) {
  const s = seed + __VU + __ITER;
  const o2 = (s % 250) + 1;
  const o3 = ((s * 7) % 250) + 1;
  const o4 = ((s * 13) % 250) + 1;
  return `10.${o2}.${o3}.${o4}`;
}

function stripTrailingSlash(value) {
  return String(value || "").replace(/\/+$/, "");
}

function formEncode(obj) {
  const pairs = [];
  for (const key in obj) {
    if (obj[key] === undefined || obj[key] === null) {
      continue;
    }
    pairs.push(`${encodeURIComponent(key)}=${encodeURIComponent(String(obj[key]))}`);
  }
  return pairs.join("&");
}

function safeJson(response) {
  try {
    return response.json();
  } catch (_err) {
    return {};
  }
}

function safeBody(response) {
  if (!response) {
    return "<no-response>";
  }
  if (response.body === undefined || response.body === null) {
    return "<empty-body>";
  }
  return String(response.body);
}

function is2xx(response) {
  return response && response.status >= 200 && response.status < 300;
}

function pad(num, size) {
  let text = String(num);
  while (text.length < size) {
    text = `0${text}`;
  }
  return text;
}

function fmt(value) {
  return Number(value || 0).toFixed(2);
}
