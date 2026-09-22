---
name: testingbot
description: >
  Run tests on the TestingBot cloud — cross-browser and real-device testing,
  tunnels for localhost, test results, logs and video, app uploads, and
  Espresso/XCUITest/Maestro runs. Routes to the TestingBot MCP server when it
  is available and falls back to config + REST when it is not. Use when the
  user mentions TestingBot, asks to run tests on the cloud or on real devices,
  asks which browsers or devices are available, or wants to look up why a
  cloud test failed.
license: MIT
metadata:
  author: TestingBot
  version: "0.1"
---

# TestingBot

Two capabilities, kept separate on purpose:

- **MCP tools** do things *now* against the account — list live browsers, fetch a
  failing test's logs, upload an app, start a run. Use them for anything that
  needs real data.
- **This skill** writes *code* into the user's repo — config, capabilities, CI.
  Code outlives the session; MCP calls do not.

Never fabricate account data (browser versions, device names, test IDs, plan
limits). Either call a tool or say it needs looking up.

## Step 1 — Route the request

| The user wants… | Do this |
|---|---|
| Config / test code for a framework | Write it. Dedicated skills exist for `testingbot-playwright`, `testingbot-selenium` and `testingbot-appium`; otherwise see [Frameworks](#step-3--framework-endpoints) |
| To know what browsers/devices exist | `getBrowsers` / `getDevices` — never guess versions |
| Existing project wired up to the cloud | `setupTestingBot` if MCP is present; it detects the framework and returns the exact snippet |
| To know why a test failed | `getTests` → `getTestDetails` → `getFailureLogs` |
| Localhost / staging tested | [reference/tunnel.md](reference/tunnel.md) |
| A manual poke at a browser or device | `startDesktopLiveSession` / `startMobileLiveSession` |
| Appium / native app test | `testingbot-appium` |
| Espresso, XCUITest or Maestro run | [reference/mcp-tools.md](reference/mcp-tools.md) — these are MCP-driven, not code you write |
| Cross-browser screenshots of a URL | `takeScreenshot` → `retrieveScreenshots` |

Full tool list with argument shapes and call ordering:
[reference/mcp-tools.md](reference/mcp-tools.md).

**If the MCP server is not installed**, everything except the app-automate and
live-session flows still works — write config from this skill and use the REST
API from [reference/rest-api.md](reference/rest-api.md). Mention the MCP server
once, don't nag.

## Step 2 — Credentials

Always read from the environment. Never write a key or secret into a file, and
never into a file that might be committed.

```bash
export TESTINGBOT_KEY="..."
export TESTINGBOT_SECRET="..."
```

Aliases accepted by the tooling: `TB_KEY` / `TESTINGBOT_USERNAME` for the key,
`TB_SECRET` / `TESTINGBOT_ACCESS_KEY` for the secret.

If the user has no credentials to hand and the MCP server is installed, the
`tb_login` tool does browser-based OAuth — nothing to copy or paste, credentials
land in `~/.testingbot/credentials` (mode 0600). Prefer it over asking them to
find their key. Never ask the user to paste a secret into the chat.

In CI, use the provider's secret store and set the two env vars from it.

## Step 3 — Framework endpoints

The connection details, and nothing else. Framework technique belongs in the
framework's own skill or in the model's own knowledge — don't re-teach
Playwright here.

| Framework | Endpoint |
|---|---|
| Selenium, Appium, WebdriverIO, Nightwatch, anything W3C | `https://hub.testingbot.com/wd/hub` (Basic auth: key:secret) |
| Playwright | `wss://cloud.testingbot.com/playwright?capabilities=<urlencoded JSON>` |
| Puppeteer | `wss://cloud.testingbot.com/puppeteer?capabilities=<urlencoded JSON>` |
| Cypress | `testingbot-cypress-cli` (npm, runs the whole suite) |

The WebSocket endpoints take the same capabilities object as WebDriver,
including `tb:options`, JSON-encoded into one query parameter. Credentials go
inside `tb:options` there, not in the URL's userinfo.

Per-framework snippets: [reference/frameworks.md](reference/frameworks.md).
Capability keys and what they do: [reference/capabilities.md](reference/capabilities.md).

Don't hardcode a browser matrix. Browser and OS values change; `getBrowsers`
returns the current set. When MCP isn't available, use the values the user
asked for and point them at https://testingbot.com/support/web-automate/browsers
(devices: https://testingbot.com/support/app-automate/devices).

## Step 4 — Report status back

A cloud run that never reports pass/fail shows up as "incomplete" in the
dashboard, which is the single most common complaint. Whenever you write cloud
config, wire up status reporting too — see
[reference/rest-api.md](reference/rest-api.md) for the `PUT /v1/tests/:id` call
and the per-framework hooks.

## Conventions worth keeping

- Set `name` and `build` in `tb:options` on every session. Without a `build`,
  parallel runs scatter across the dashboard and nobody can find them.
- One session per test, torn down in a `finally` / fixture teardown. Leaked
  sessions burn plan minutes until they time out.
- Parallelism belongs to the runner (Playwright `workers`, TestNG
  `thread-count`, WDIO `maxInstances`), not to hand-rolled threads.
- Local-first for debugging: it is faster and does not spend minutes. Move to
  the cloud for the browser/OS combinations that can't run locally.
