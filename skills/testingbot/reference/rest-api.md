# REST API

Base: `https://api.testingbot.com/v1`. HTTP Basic auth with key and secret over
HTTPS. Use this when the MCP server isn't installed, and for the one thing that
belongs *inside* the test run: reporting pass/fail.

Rate limit: 2000 requests / 5 minutes per key. Responses carry
`X-RateLimit-Remaining`; a `429` comes with `Retry-After`, and retrying after
that many seconds is safe.

## Mark a test passed or failed

A session ends in "incomplete" unless something reports its outcome. The
framework knows the result; TestingBot doesn't until you tell it.

```bash
curl -X PUT "https://api.testingbot.com/v1/tests/$SESSION_ID" \
  -u "$TESTINGBOT_KEY:$TESTINGBOT_SECRET" \
  -d "test[success]=1" \
  -d "test[name]=Checkout flow"
```

`test[success]` is `1` or `0`. The session ID comes from the driver:

| Framework | Session ID |
|---|---|
| Selenium (JS) | `(await driver.getSession()).getId()` |
| Selenium (Python) | `driver.session_id` |
| Selenium (Java) | `((RemoteWebDriver) driver).getSessionId().toString()` |
| WebdriverIO | `browser.sessionId` |
| Playwright / Puppeteer | `page.evaluate(_ => {}, `testingbot_executor: {"action":"getSessionDetails"}`)` returns `{ sessionId }` |

Wire this into the teardown hook, not the test body, so it runs on failure too:
`afterEach` (Mocha/Jest), `@AfterMethod` (TestNG), a `yield` fixture (pytest),
`after` hook (WDIO — though `@wdio/testingbot-service` does it for you).

Where a TestingBot service or client library exists, use it instead of
hand-rolling the HTTP call: `@wdio/testingbot-service` for WebdriverIO, the
`testingbot-api` npm package (`tb.updateTest({ 'test[success]': passed,
'test[name]': name }, sessionId, cb)`) elsewhere in JS.

Playwright and Puppeteer have a better option — `setSessionStatus` over
`testingbot_executor`, no REST call and no session ID lookup. See the
`testingbot-playwright` skill.

## Other endpoints

| Call | Purpose |
|---|---|
| `GET /tests` | Recent sessions |
| `GET /tests/:id` | One session: status, video, logs |
| `DELETE /tests/:id` | Delete a session |
| `PUT /tests/:id/stop` | Stop a running session |
| `GET /builds`, `GET /builds/:id/tests` | Builds |
| `GET /browsers` | Available browsers — the machine-readable browser matrix |
| `GET /devices` | Available devices |
| `GET /tunnel/list`, `DELETE /tunnel/:id` | Tunnels |
| `GET /user` | Plan, minutes used, parallel limit |
| `POST /storage` | Upload an app |

Append `?omit=field1,field2` to trim the response body.

Full spec: `https://testingbot.com/api/v1/openapi.json` — fetch it rather than
guessing a parameter name.
