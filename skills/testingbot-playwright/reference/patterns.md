# Playwright + TestingBot patterns

## Testing localhost

The cloud browser can't see the dev server. Start a tunnel and it can.

Manual:

```bash
java -jar testingbot-tunnel.jar "$TESTINGBOT_KEY" "$TESTINGBOT_SECRET"
# wait for "You may start tests"
npx playwright test
```

Automated, so the suite is self-contained:

```typescript
// global-setup.ts
import testingbotTunnel from 'testingbot-tunnel-launcher';

export default async function globalSetup() {
  const tunnel = await new Promise((resolve, reject) => {
    testingbotTunnel(
      { apiKey: process.env.TESTINGBOT_KEY, apiSecret: process.env.TESTINGBOT_SECRET },
      (err: Error, t: any) => (err ? reject(err) : resolve(t)),
    );
  });
  (globalThis as any).__tbTunnel = tunnel;
}
```

```typescript
// playwright.config.ts
export default defineConfig({
  globalSetup: './global-setup.ts',
  globalTeardown: './global-teardown.ts',   // tunnel.close()
  use: { baseURL: 'http://localhost:3000', connectOptions: { wsEndpoint } },
});
```

Close the tunnel in `globalTeardown`. A leaked tunnel process outlives the run
and confuses the next one.

Don't start a tunnel when `baseURL` is public — it's a process to babysit for
no benefit.

## Reusing one config for local and cloud

Keep a single config; switch on an env var. Saves maintaining two files that
drift.

```typescript
const useCloud = !!process.env.TB_CLOUD;

export default defineConfig({
  use: useCloud ? { connectOptions: { wsEndpoint } } : {},
  projects: useCloud ? cloudProjects : [{ name: 'local', use: devices['Desktop Chrome'] }],
});
```

```bash
npx playwright test                 # local
TB_CLOUD=1 npx playwright test      # cloud matrix
```

## Real mobile devices

Playwright's `devices['iPhone 13']` is *emulation* — a resized Chromium with a
spoofed user agent. It catches layout bugs and nothing else. When the user says
"real device", they need a real one, and that means either the device
parameters on the connect endpoint or Appium.

Check what's actually available with `getDevices` before naming a model. Verify
current Playwright real-device support at
https://testingbot.com/support/playwright — don't assume from the desktop
endpoint.

## Traces, video, screenshots

TestingBot records video of the session server-side; Playwright records its own
trace client-side. They're complementary — the trace has the DOM snapshots, the
video shows what the VM actually displayed.

```typescript
use: {
  trace: 'on-first-retry',
  screenshot: 'only-on-failure',
  video: 'off',            // TestingBot already records it; don't pay twice
}
```

## GitHub Actions

```yaml
name: e2e
on: [push]

jobs:
  cross-browser:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 22, cache: npm }
      - run: npm ci
      - run: npx playwright test
        env:
          TESTINGBOT_KEY: ${{ secrets.TESTINGBOT_KEY }}
          TESTINGBOT_SECRET: ${{ secrets.TESTINGBOT_SECRET }}
          TB_CLOUD: "1"
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report
          path: playwright-report/
```

No `npx playwright install` — browsers live on the cloud. That's a meaningful
chunk of CI time saved, worth mentioning to the user.

If the app runs in the same job, add the tunnel action before the test step:

```yaml
      - uses: testingbot/testingbot-tunnel-action@v1
        with:
          key: ${{ secrets.TESTINGBOT_KEY }}
          secret: ${{ secrets.TESTINGBOT_SECRET }}
```

## Sharding

Playwright's built-in sharding works unchanged, but total concurrency is
`shards × workers` and it must stay under the account's parallel limit.

```yaml
strategy:
  matrix:
    shard: [1, 2, 3, 4]
steps:
  - run: npx playwright test --shard=${{ matrix.shard }}/4
```

With `workers: 3` and 4 shards that's 12 concurrent sessions. Check
`getUserInfo` before suggesting numbers.

Pass the same `build` value to every shard so the dashboard shows one build.

## Session hygiene

- One browser per worker, torn down by the fixture. Never `connect()` in a test
  body without a matching `close()` in a `finally`.
- Set `name` per test if you want readable dashboard entries — `testInfo.title`
  is right there.
- A suite that dies mid-run leaves sessions open until they idle out. `stopTest`
  kills a specific one; `getTests` finds them.
