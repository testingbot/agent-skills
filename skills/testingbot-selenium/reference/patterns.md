# Selenium + TestingBot patterns

## Cross-browser matrices

Drive the matrix from the test runner's own parametrisation, not from a loop
inside a test. The runner then reports one result per combination.

TestNG — a data provider or `<parameter>` entries per `<test>` block:

```xml
<suite name="cross-browser" parallel="tests" thread-count="3">
  <test name="chrome-win11">
    <parameter name="browser" value="chrome"/>
    <parameter name="platform" value="WIN11"/>
    <classes><class name="tests.CheckoutTest"/></classes>
  </test>
  <test name="safari-mac">
    <parameter name="browser" value="safari"/>
    <parameter name="platform" value="SONOMA"/>
    <classes><class name="tests.CheckoutTest"/></classes>
  </test>
</suite>
```

pytest — parametrise the driver fixture:

```python
@pytest.fixture(params=[
    ('chrome', 'WIN11'),
    ('firefox', 'WIN11'),
    ('safari', 'SONOMA'),
])
def driver(request):
    browser, platform = request.param
    ...
```

Give every combination in one run the same `build` value so they group into a
single build in the dashboard.

## Parallel limits

Total concurrency is `runner threads × CI matrix jobs`. It must stay at or
below the account's parallel limit, which `getUserInfo` reports. Exceeding it
does not error — sessions queue, then tests time out waiting for a browser.
That failure looks exactly like flakiness, and is the most common false alarm.

## Testing localhost

The cloud browser can't reach the dev server. Start a tunnel, then point the
driver at the local endpoint:

```
https://hub.testingbot.com/wd/hub   →   http://localhost:4445/wd/hub
```

Nothing else changes — same capabilities, same code. Full detail in
`reference/tunnel.md` of the `testingbot` skill. For parallel CI jobs that each
need their own tunnel, use `tunnelIdentifier`.

Only do this when the target really is internal. A public staging URL needs no
tunnel.

## GitHub Actions

```yaml
name: e2e
on: [push]

jobs:
  cross-browser:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with: { distribution: temurin, java-version: '21', cache: maven }
      - run: mvn -B test
        env:
          TESTINGBOT_KEY: ${{ secrets.TESTINGBOT_KEY }}
          TESTINGBOT_SECRET: ${{ secrets.TESTINGBOT_SECRET }}
          BUILD_NUMBER: ${{ github.run_id }}
```

No browser or driver installation step — they live on the cloud. That is a real
chunk of CI time saved and worth pointing out.

Add the tunnel before the test step if the app runs in the same job:

```yaml
      - uses: testingbot/testingbot-tunnel-action@v1
        with:
          key: ${{ secrets.TESTINGBOT_KEY }}
          secret: ${{ secrets.TESTINGBOT_SECRET }}
```

Jenkins, TeamCity, Buildkite, Azure DevOps, Gradle and fastlane all have
official TestingBot plugins — prefer one over scripting the tunnel by hand.

## Selenium Grid

An existing Grid setup can point its nodes at TestingBot rather than being
replaced. Useful when a team has Grid-shaped infrastructure they don't want to
rewrite. See https://testingbot.com/support/web-automate/selenium/grid.

For new work, connect to the hub directly — a Grid in front of it is a hop that
buys nothing.

## Screen resolution and window size

The VM boots at `1280x1024` unless `screen-resolution` says otherwise. A test
asserting on layout, or taking screenshots for comparison, should set it
explicitly rather than relying on the default staying put:

```java
tbOptions.put("screen-resolution", "1920x1080");
```

Maximising the window is not the same thing — it maximises within whatever
resolution the VM has.

## Flakiness that is actually configuration

| Symptom | Usual cause |
|---|---|
| Session never starts | TestingBot key at the top level of capabilities instead of in `tb:options` |
| Tests time out at the start, intermittently | Concurrency above the account's parallel limit |
| Works locally, blank page on cloud | App not reachable — needs a tunnel |
| Passes alone, fails in the suite | Shared driver across tests |
| Dashboard shows "incomplete" | Nothing reports `tb:test-result` |
| Fails only on one browser | A real browser difference — suspect the app |
