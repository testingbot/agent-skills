---
name: testingbot-playwright
description: >
  Write, configure and debug Playwright tests that run on TestingBot's cloud
  browsers and real devices. Covers the wss connect endpoint, the capabilities
  object, running one suite across many browsers, marking sessions
  passed/failed with testingbot_executor, tunnels for localhost, and CI. Use
  when the user asks to run Playwright on TestingBot or in the cloud, test
  Safari or WebKit or a browser they can't run locally, go cross-browser, or
  debug a Playwright test that only fails on the cloud.
license: MIT
metadata:
  author: TestingBot
  version: "0.1"
---

# Playwright on TestingBot

## Step 1 — Local or cloud?

Default to local. Cloud costs minutes and is slower to iterate on.

| The user says | Target |
|---|---|
| Nothing about the cloud, "locally", "debug this" | Local |
| "TestingBot", "cloud", "cross-browser", "real device" | Cloud |
| A combination that can't run locally — Safari on Windows, a real iPhone, an old Chrome | Cloud |
| Ambiguous | Local, and mention that cloud is one config block away |

A cloud run only changes *where the browser is*. Test bodies, fixtures, page
objects and assertions are unchanged. Never rewrite tests to "make them work on
the cloud" — if a test needs changing, that's a bug worth understanding.

## Step 2 — Connect

Build a capabilities object, JSON-encode it into the `capabilities` query
parameter. TestingBot-specific keys go in `tb:options`, exactly as they do for
Selenium.

```typescript
// playwright.config.ts
import { defineConfig } from '@playwright/test';

const capabilities = {
  browserName: 'chrome',
  browserVersion: 'latest',
  platform: 'Windows 11',
  'tb:options': {
    key: process.env.TB_KEY,
    secret: process.env.TB_SECRET,
    name: 'My suite',
    build: process.env.GITHUB_RUN_ID ?? 'local',
  },
};

const wsEndpoint =
  `wss://cloud.testingbot.com/playwright?capabilities=${encodeURIComponent(JSON.stringify(capabilities))}`;

export default defineConfig({
  use: { connectOptions: { wsEndpoint } },
});
```

Details that matter:

- **`platform`, not `os`.** `platform` (or `platformName`) takes a readable
  name: `Windows 11`, `Windows 10`, `LINUX`. There is no `os` parameter — a
  config using one silently gets the default platform.
- **Credentials belong in `tb:options`.** `key`/`secret` are also accepted at
  the top level of the capabilities object, or as flat `?key=&secret=` query
  parameters. Prefer `tb:options`; it is the documented form and it keeps one
  object to pass around.
- `connectOptions` in config keeps every test using the remote browser and lets
  Playwright's fixture handle teardown. Hand-rolled `connect()` calls leak
  sessions.
- Outside `@playwright/test`, connect with `playwright-core` —
  `playwright.connect({ wsEndpoint })` or `playwright.chromium.connect(...)`.
  No need for the full `playwright` package and its browser download.

Call the MCP `getBrowsers` tool for current `browserName` / `browserVersion` /
platform values rather than trusting a hardcoded table.

## Step 3 — Many browsers, one suite

This is the reason to be on the cloud at all. One project per target:

```typescript
import { defineConfig } from '@playwright/test';

const tbOptions = {
  key: process.env.TB_KEY,
  secret: process.env.TB_SECRET,
  build: process.env.GITHUB_RUN_ID ?? 'local',
};

function tb(caps: Record<string, string>) {
  const capabilities = { ...caps, 'tb:options': tbOptions };
  return {
    connectOptions: {
      wsEndpoint:
        `wss://cloud.testingbot.com/playwright?capabilities=${encodeURIComponent(JSON.stringify(capabilities))}`,
    },
  };
}

export default defineConfig({
  workers: 5,            // keep at or below the account's parallel limit
  retries: process.env.CI ? 1 : 0,
  projects: [
    { name: 'chrome-win',  use: tb({ browserName: 'chrome',  browserVersion: 'latest', platform: 'Windows 11' }) },
    { name: 'firefox-win', use: tb({ browserName: 'firefox', browserVersion: 'latest', platform: 'Windows 11' }) },
    { name: 'safari-mac',  use: tb({ browserName: 'safari',  browserVersion: 'latest', platform: 'Sonoma' }) },
  ],
});
```

Two things to get right:

- **`workers` must not exceed the plan's parallel limit.** Over it, sessions
  queue and tests time out waiting for a browser — which reads as flakiness.
  `getUserInfo` reports the limit.
- **One `build` value across all projects**, so the whole matrix lands in one
  build in the dashboard. A CI run ID is the natural choice.

## Step 4 — Report pass/fail

A session shows as incomplete until something reports its outcome. Playwright
talks to TestingBot through `page.evaluate` with a `testingbot_executor:`
payload — the first argument is an ignored no-op function, the payload rides in
the second.

```typescript
await page.evaluate(_ => {}, `testingbot_executor: ${JSON.stringify({
  action: 'setSessionStatus',
  arguments: { passed: true, reason: 'Title matched' },
})}`);
```

Actions: `setSessionStatus` (`passed`, `reason`), `setSessionName` (`name`),
`getSessionDetails` (returns `{ sessionId }` — use it for REST calls).

Wire it into a fixture so it also runs when a test fails:

```typescript
// fixtures.ts
import { test as base } from '@playwright/test';

export const test = base.extend<{ tbStatus: void }>({
  tbStatus: [async ({ page }, use, testInfo) => {
    await page.evaluate(_ => {}, `testingbot_executor: ${JSON.stringify({
      action: 'setSessionName',
      arguments: { name: testInfo.title },
    })}`);

    await use();

    const passed = testInfo.status === testInfo.expectedStatus;
    await page.evaluate(_ => {}, `testingbot_executor: ${JSON.stringify({
      action: 'setSessionStatus',
      arguments: { passed, reason: testInfo.error?.message ?? '' },
    })}`);
  }, { auto: true }],
});
```

The same mechanism drives visual testing — `visual.snapshot` and
`visual.baseline` return a result object with a `match` field, so capture the
return value and assert on it.

## Step 5 — Mobile

Set `deviceName` inside `tb:options`. Add `realDevice: true` for a real handset
rather than an emulator or simulator:

```typescript
const capabilities = {
  browserName: 'chrome',
  browserVersion: 'latest',
  platform: 'Android',
  'tb:options': {
    key: process.env.TB_KEY,
    secret: process.env.TB_SECRET,
    deviceName: 'Pixel 9',
    realDevice: true,
  },
};
```

Playwright's own `devices['iPhone 13']` is emulation — a resized Chromium with
a spoofed user agent. Don't present it as real-device testing. Confirm a model
exists with `getDevices` before naming one.

## Step 6 — Other languages

Same endpoint, same capabilities object; only the connect call differs.

```python
# Python
import json, os
from urllib.parse import quote
from playwright.sync_api import sync_playwright

caps = {
    "browserName": "chrome",
    "browserVersion": "latest",
    "platform": "Windows 11",
    "tb:options": {"key": os.environ["TB_KEY"], "secret": os.environ["TB_SECRET"]},
}
ws = "wss://cloud.testingbot.com/playwright?capabilities=" + quote(json.dumps(caps))

with sync_playwright() as p:
    browser = p.chromium.connect(ws)
    page = browser.new_page()
```

```ruby
# Ruby — status reporting takes a single string argument
page.evaluate("testingbot_executor: #{JSON.generate({ action: 'setSessionStatus', arguments: { passed: true } })}")
```

Java: `playwright.chromium().connect(wsEndpoint)`.
C#: `await playwright.Chromium.ConnectAsync(wsEndpoint)`.

Always `chromium.connect()` regardless of the target browser — `browserName`
selects what actually launches. Using `firefox.connect()` for a Firefox target
is a natural guess and it is wrong.

## Step 7 — Debugging a test that only fails on the cloud

In order, stopping when you find it:

1. **Does it pass locally on the same browser?** If not, it's not a cloud
   problem.
2. **Is the app reachable?** A `localhost` or staging URL needs a tunnel — see
   [reference/patterns.md](reference/patterns.md).
3. **Timing.** Cloud round-trips are slower. The fix is a web-first assertion
   (`await expect(locator).toBeVisible()`), never `waitForTimeout`. Raise
   `navigationTimeout` / `actionTimeout` in config rather than sprinkling waits.
4. **Viewport.** The cloud VM's screen isn't the local default; set an explicit
   `viewport` if layout assertions differ.
5. **Look at the evidence.** `getTests` → `getTestDetails` gives video and
   screenshots; `getFailureLogs` with type `browser` gives console errors.
   Watch the video before theorising.
6. **A genuine browser difference.** WebKit differs from Chromium in real ways.
   If Safari alone fails, suspect the app, not the harness.

## Don't

- Don't set `headless: false` for a cloud run — it means nothing remotely.
  (`headless` and `headful` are TestingBot capabilities; that's a different
  thing from Playwright's launch option.)
- Don't use `channel: 'chrome'` with `connectOptions`; the remote end picks the
  browser.
- Don't download traces for every passing test in CI. `trace: 'on-first-retry'`.
- Don't put the key or secret in `playwright.config.ts` as a literal. Env vars,
  always.
