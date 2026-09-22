# TestingBot MCP tools

Tool names as registered by `@testingbot/mcp-server`. If a call fails with an
auth error, the fix is `tb_login` — not editing JSON config.

## Auth

| Tool | Use |
|---|---|
| `tb_login` | Browser OAuth (loopback) or device-code flow on SSH/containers. Pass `mode: "device"` to force the code flow. Writes `~/.testingbot/credentials`. |

Credential precedence: env vars → `~/.testingbot/credentials` → degraded mode
where every tool but `tb_login` refuses.

## Capacity — what exists right now

| Tool | Use |
|---|---|
| `getBrowsers` | Available browsers/platforms. `type: "web" \| "mobile"`. |
| `getDevices` | Real devices and simulators, with an `available` flag. |

Call these before writing a capability block that names a specific version.
They are the authoritative source; the published lists at
https://testingbot.com/support/web-automate/browsers and
https://testingbot.com/support/app-automate/devices lag behind them.

## Results and debugging

Normal failure-triage order:

1. `getTests` — recent sessions, paginated.
2. `getTestDetails` — one session by ID: status, video, screenshots, metadata.
3. `getFailureLogs` — the actual log content. Types: `selenium`, `browser`,
   `chrome`, `vm`, `appium`. Start with `selenium` for WebDriver runs and
   `browser` for console errors.

| Tool | Use |
|---|---|
| `getTests`, `getTestDetails` | List / inspect sessions |
| `getFailureLogs` | Log file content for a session |
| `updateTest` | Set name/status after the fact |
| `stopTest` | Kill a running session |
| `deleteTest` | Destructive — confirm with the user first |
| `getBuilds`, `getTestsForBuild` | Group sessions by build |
| `deleteBuild` | Destructive — deletes the build *and its tests*. Confirm. |

## Tunnels

| Tool | Use |
|---|---|
| `getTunnelList` | Active tunnels (check here before telling someone to start one) |
| `deleteTunnel` | Terminate a tunnel by ID |

These inspect tunnels; they don't start one. Starting a tunnel is a local
process — see [tunnel.md](tunnel.md).

## Project setup

| Tool | Use |
|---|---|
| `listTestFiles` | Read-only scan for test files by detected framework |
| `setupTestingBot` | Detects the framework and returns a ready-to-paste config snippet |

`setupTestingBot` covers playwright, cypress, webdriverio, selenium-js,
nightwatch, puppeteer, vitest, jest, mocha, plus espresso/xcuitest/maestro.
Prefer it over writing config from memory when it is available — it is
generated from the same source as the platform. Take its output and adapt it to
the project's conventions rather than pasting it blind.

## Mobile app testing

Storage:

| Tool | Use |
|---|---|
| `uploadFile` | Upload a local APK/IPA/ZIP → returns an `app_url` |
| `uploadRemoteFile` | Same, from a URL |
| `getStorageFiles`, `deleteStorageFile` | Manage storage |

Espresso / XCUITest — the run is async, so poll:

1. `uploadAppAutomateApp` (app under test) → `projectId`
2. `uploadAppAutomateTests` (instrumented APK, or `.ipa`/`.xctestrun` bundle)
3. `runAppAutomateTest` → returns a run ID immediately, does **not** block
4. `getAppAutomateRunStatus` → poll
5. `getAppAutomateRunResults` → per-run outcomes plus JUnit XML

Maestro — same async shape:

1. `maestroCheatSheet` — flow YAML syntax; read it before writing a flow
2. `uploadMaestroApp`, `uploadMaestroFlows`, optionally
   `uploadMaestroCompanionApp`
3. `runMaestroTest` → run ID, returns immediately
4. `getMaestroRunStatus` → poll; `getMaestroRunResults` → failures first
5. `getMaestroFlowDetails` — step-level detail for one flow
6. `cancelMaestroRun`, `retryMaestroRun` (pass `flowId` to retry one flow)

`listMaestroProjects` / `listMaestroRuns` find an earlier run by name.

Don't busy-poll. Report the run ID to the user, poll at a sane interval, and
say what you're waiting on.

## Live sessions

| Tool | Use |
|---|---|
| `startLiveSession` | Generic; needs `platformType` |
| `startDesktopLiveSession` | Desktop browser, sets `platformType` for you |
| `startMobileLiveSession` | Mobile device, same |

These open an interactive session for a human. Offer one when someone wants to
*look* at a bug rather than automate it.

## Screenshots

`takeScreenshot` (URL across browsers) → returns an ID → `retrieveScreenshots`.
`getScreenshotList` for history. Cheaper than a full session when the question
is only "how does this render".

## Account

`getUserInfo` (minutes used, plan), `updateUserInfo`, `getTeam`,
`getUsersInTeam`, `getUserFromTeam`. Reach for `getUserInfo` when a run fails
in a way that smells like exhausted plan minutes or parallel limits.
