---
name: testingbot-selenium
description: >
  Write, configure and debug Selenium WebDriver tests that run on TestingBot's
  cloud browsers, in Java, Python, C#, Ruby, JavaScript or PHP. Covers the hub
  URL, W3C capabilities and tb:options, marking tests passed or failed,
  retrieving the session ID, running suites in parallel, tunnels for localhost,
  and CI. Use when the user asks to run Selenium or WebDriver tests on
  TestingBot or in the cloud, test a browser they can't run locally, go
  cross-browser, or debug a Selenium test that only fails on the cloud.
license: MIT
metadata:
  author: TestingBot
  version: "0.1"
---

# Selenium on TestingBot

## Step 1 — Local or cloud?

Default to local. Cloud costs minutes and is slower to iterate on.

| The user says | Target |
|---|---|
| Nothing about the cloud, "locally", "debug this" | Local |
| "TestingBot", "cloud", "cross-browser", "real device" | Cloud |
| A combination that can't run locally — Safari on Windows, IE, an old Chrome | Cloud |
| Ambiguous | Local, and mention that cloud is a URL and a capability block away |

Moving a suite to the cloud changes the driver construction and nothing else.
Page objects, waits and assertions stay as they are.

## Step 2 — Connect

Point a `RemoteWebDriver` at the hub. Two equivalent ways to authenticate —
pick one and be consistent:

```
https://KEY:SECRET@hub.testingbot.com/wd/hub    # credentials in the URL
https://hub.testingbot.com/wd/hub               # credentials in tb:options
```

The second is cleaner: nothing secret ends up in a URL that gets logged by a
driver or a proxy. Prefer it unless the surrounding code already does the other.

```java
ChromeOptions options = new ChromeOptions();
options.setPlatformName("WIN11");
options.setBrowserVersion("latest");
options.setCapability("tb:options", Map.of(
    "key", System.getenv("TESTINGBOT_KEY"),
    "secret", System.getenv("TESTINGBOT_SECRET"),
    "name", "Checkout flow",
    "build", System.getenv("BUILD_NUMBER")));

WebDriver driver = new RemoteWebDriver(
    URI.create("https://hub.testingbot.com/wd/hub").toURL(), options);
```

Python, C#, Ruby, JavaScript and PHP: [reference/languages.md](reference/languages.md).

## Step 3 — Capabilities

TestingBot is W3C compliant. Standard keys — `browserName`, `browserVersion`,
`platformName` — go at the top level. Everything TestingBot-specific goes
inside `tb:options`. A TestingBot key at the top level is rejected by a strict
W3C endpoint, and that is the single most common setup failure.

```javascript
{
  browserName: 'chrome',
  browserVersion: 'latest',
  platformName: 'WIN11',
  'tb:options': { name: 'Checkout flow', build: 'ci-1042' }
}
```

`platformName` takes short codes in the Selenium docs — `WIN11`, `WIN10`,
`LINUX` — and readable names also work. Don't hardcode a browser matrix; call
the MCP `getBrowsers` tool for the current set.

Always set `name` and `build`. Without `build`, a parallel run scatters across
the dashboard and nobody can find the failure. Use the CI run ID.

Full capability list — video, logs, timezone, resolution, geolocation, tunnel,
driver pinning: `reference/capabilities.md` in the `testingbot` skill.

## Step 4 — Report pass/fail

A session is "incomplete" until something reports its outcome. Selenium has two
routes; use the first unless the result isn't known until after the session is
gone.

**In-test, via the JavaScript executor.** No API call, no session ID:

```java
((JavascriptExecutor) driver).executeScript("tb:test-name=Checkout flow");
((JavascriptExecutor) driver).executeScript("tb:test-result=passed");
```

```python
driver.execute_script('tb:test-name=Checkout flow')
driver.execute_script('tb:test-result=passed')   # or 'failed'
```

Same string in every language — `driver.executeScript`,
`$web_driver->executeScript`, `((IJavaScriptExecutor)driver).ExecuteScript`.

**After the session, via the API client.** Needs the session ID, captured while
the driver is alive:

| Language | Session ID |
|---|---|
| Java | `driver.getSessionId().toString()` |
| Python | `driver.session_id` |
| JavaScript | `(await driver.getSession()).getId()` |
| C# | `((RemoteWebDriver)driver).SessionId.ToString()` |
| Ruby | `driver.session_id` |
| PHP | `$driver->getSessionID()` |

```python
from testingbotclient import TestingBotClient
tb = TestingBotClient(key, secret)
tb.tests.update_test(session_id, name='Checkout flow', passed=True)
```

Clients: `testingbot-api` (npm), `testingbotclient` (pip), `testingbot` (gem),
`TestingbotREST` (Java), `TestingBot\TestingBotAPI` (PHP). Raw REST in
`reference/rest-api.md` of the `testingbot` skill.

Put either call in the teardown hook — `@AfterMethod`, `tearDown`, a `yield`
fixture, `afterEach` — so it runs when the test fails. Inside the test body it
only runs on success, which is exactly backwards.

## Step 5 — Parallel suites

Parallelism belongs to the test runner, never to hand-rolled threads. One
driver per test, torn down in the runner's teardown.

- TestNG: `parallel="methods"` with `thread-count`
- JUnit 5: `junit.jupiter.execution.parallel.enabled`
- pytest: `pytest-xdist`, `-n 5`
- NUnit: `[Parallelizable]` + `LevelOfParallelism`

Keep the thread count at or below the account's parallel limit — `getUserInfo`
reports it. Over the limit, sessions queue and time out waiting for a browser,
which reads as flakiness and is not.

Cross-browser matrices, CI, tunnels and Grid:
[reference/patterns.md](reference/patterns.md).

## Step 6 — Debugging a test that only fails on the cloud

In order, stopping when you find it:

1. **Does it pass locally on the same browser and version?** If not, it isn't a
   cloud problem.
2. **Is the app reachable?** `localhost`, a private IP or an internal host needs
   a tunnel — `reference/tunnel.md` in the `testingbot` skill.
3. **Capability shape.** A session that fails to start at all is nearly always
   a TestingBot key left at the top level instead of inside `tb:options`.
4. **Timing.** Cloud latency is higher than local. Use explicit waits
   (`WebDriverWait` on a condition), never `Thread.sleep`.
5. **Window size.** The VM's default resolution differs from the local one. Set
   `screen-resolution` or maximise explicitly before layout assertions.
6. **Look at the evidence.** `getTests` → `getTestDetails` for video and
   screenshots, `getFailureLogs` with type `selenium` for the command log and
   `browser` for console errors. Watch the video before theorising.

## Don't

- Don't put `name`, `build` or any `tb:` key at the top level of capabilities.
- Don't pin `seleniumVersion` or a driver version without a reason; TestingBot
  picks a compatible pair and a pin is future breakage.
- Don't share one driver across tests to "save time" — a leaked session burns
  plan minutes until it idles out.
- Don't hardcode credentials. Env vars, always.
- Don't use the deprecated JSONWP protocol for new work; W3C is the default.
