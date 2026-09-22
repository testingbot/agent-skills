---
name: testingbot-appium
description: >
  Write, configure and debug Appium tests for native, hybrid and Flutter mobile
  apps on TestingBot's real devices, emulators and simulators. Covers uploading
  the app binary, the hub URL, appium: and tb:options capabilities, real device
  vs emulator, Appium version pinning, permissions, locale and orientation,
  marking tests passed or failed, and app instrumentation. Use when the user
  asks to run Appium or mobile app tests on TestingBot, test an APK or IPA, test
  on a real iPhone or Android device, or debug a mobile test that only fails on
  the cloud.
license: MIT
metadata:
  author: TestingBot
  version: "0.1"
---

# Appium on TestingBot

## Step 1 — Is Appium the right product?

TestingBot runs four different mobile things. Picking wrong wastes the whole
setup.

| The user has | Product | How it runs |
|---|---|---|
| Appium tests (any language), native or hybrid app | **Appium** — this skill | Their runner drives a remote session |
| An Espresso or XCUITest suite | **App Automate** | TestingBot runs the suite; MCP tools |
| Maestro flow YAML | **Maestro** | TestingBot runs the flows; MCP tools |
| A mobile *website*, not an app | **Selenium or Playwright** | `testingbot-selenium` / `testingbot-playwright` |

For App Automate and Maestro, see `reference/mcp-tools.md` in the `testingbot`
skill — those are upload-and-poll flows, not code you write.

## Step 2 — Upload the app

The device needs the binary. Either a public URL, or upload once and reference
the returned ID.

With the MCP server: `uploadFile` (local `.apk`/`.ipa`/`.zip`) or
`uploadRemoteFile` (from a URL). Otherwise:

```bash
curl -u "$TESTINGBOT_KEY:$TESTINGBOT_SECRET" \
  -X POST "https://api.testingbot.com/v1/storage" \
  -F "file=@/path/to/app.apk"
```

```json
{"app_url":"tb://YOUR_APP_ID"}
```

Pass that `tb://` value as `appium:app`. Uploading on every CI run is wasteful
for a build that hasn't changed — upload per build, reuse the ID across the
matrix. `getStorageFiles` lists what's already there.

## Step 3 — Connect

```python
capabilities = {
    "platformName": "Android",
    "appium:automationName": "UiAutomator2",   # XCUITest for iOS
    "appium:deviceName": "Galaxy S24",
    "appium:platformVersion": "14.0",
    "appium:app": "tb://YOUR_APP_ID",
    "tb:options": {
        "key": os.environ["TESTINGBOT_KEY"],
        "secret": os.environ["TESTINGBOT_SECRET"],
        "name": "Login flow",
        "build": os.environ.get("BUILD_NUMBER", "local"),
        "realDevice": True,
    },
}

options = AppiumOptions().load_capabilities(capabilities)
driver = webdriver.Remote("https://hub.testingbot.com/wd/hub", options=options)
```

Three namespaces, and mixing them up is the most common failure:

- **`platformName`** — bare, W3C standard.
- **`appium:*`** — everything Appium defines: `deviceName`, `platformVersion`,
  `automationName`, `app`, `autoGrantPermissions`, `locale`, `orientation`.
  Appium 2 and 3 require the prefix; an unprefixed `deviceName` is rejected.
- **`tb:options`** — everything TestingBot defines: credentials, `name`,
  `build`, `realDevice`, `appiumVersion`.

Credentials can instead go in the hub URL
(`https://KEY:SECRET@hub.testingbot.com/wd/hub`). Prefer `tb:options` — nothing
secret then ends up in a URL a driver might log.

Java, C#, Ruby, JavaScript and PHP: [reference/languages.md](reference/languages.md).

## Step 4 — Real device or emulator?

`realDevice: true` inside `tb:options` selects physical hardware. Without it
you get an Android emulator or iOS simulator.

Choose deliberately, and say which you chose:

| Use a real device for | An emulator/simulator is fine for |
|---|---|
| Performance, camera, biometrics, push, SIM behaviour | Layout, navigation, business logic |
| Anything shipping-critical before release | Fast feedback on every commit |
| Bugs that "only happen on device" | Broad OS-version matrices, cheaply |

Real devices are a finite pool. Pin an exact model and the test queues when
it's busy; `appium:deviceName` accepts a pattern — `"iPhone.*"`, `"Galaxy S.*"`
— which grabs the first free match. Prefer a pattern unless the test is about
one specific handset.

Confirm a model exists with the MCP `getDevices` tool; it reports availability.
Don't name devices from memory.

## Step 5 — Report pass/fail

Same JavaScript-executor annotation as Selenium, and it needs no session ID or
API call:

```python
driver.execute_script('tb:test-name=Login flow')
driver.execute_script('tb:test-result=passed')   # or 'failed'
```

```java
((JavascriptExecutor) driver).executeScript("tb:test-result=failed");
```

Put it in teardown — `@AfterMethod`, `[TearDown]`, a `yield` fixture — so it
runs when the test fails. Inside the test body it only fires on success, which
is backwards. Without it, every session shows as "incomplete".

The REST route (`PUT /v1/tests/:id`) is there for results only known after the
session ends — see `reference/rest-api.md` in the `testingbot` skill.

## Step 6 — Common options

| Need | Capability |
|---|---|
| Dismiss permission dialogs automatically | `appium:autoGrantPermissions: true` |
| Locale | `appium:locale` — Android takes `ES`, iOS takes `es_ES` |
| Landscape | `appium:orientation: "LANDSCAPE"` |
| Pin the Appium version | `tb:options.appiumVersion` — `latest`, `latest-1`, or `3.2.2` |
| Install a second app mid-test | `driver.execute_script('mobile: installApp', {'appPath': 'tb://...'})` |

Biometrics, incoming calls and SMS, and camera image injection need app
instrumentation — see [reference/capabilities.md](reference/capabilities.md).

Leave `appiumVersion` unset unless reproducing a specific failure. Note that
Appium 3 prefixes security-flagged commands (`adb_shell` became
`uiautomator2:adb_shell`), so a suite pinned to 2.x may need edits when it moves.

## Step 7 — Debugging a test that only fails on the cloud

In order, stopping when you find it:

1. **Did the session start at all?** If not, it's capabilities — almost always
   a missing `appium:` prefix, or a TestingBot key left outside `tb:options`.
2. **Is it the right build?** A stale `tb://` ID silently tests yesterday's
   APK. Re-upload and compare IDs.
3. **Real device vs emulator.** A test that passes on an emulator and fails on
   hardware is usually finding a genuine bug — timing, permissions, or a
   hardware feature the emulator fakes.
4. **Permissions.** An unexpected system dialog blocks everything after it.
   `autoGrantPermissions` handles the common case.
5. **Timing.** App launch on a real device is slower than local. Explicit waits
   on conditions, never fixed sleeps.
6. **Look at the evidence.** `getTests` → `getTestDetails` for video,
   `getFailureLogs` with type `appium` for the server log. Watch the video
   before theorising.

## Don't

- Don't drop the `appium:` prefix — Appium 2 and 3 reject bare vendor
  capabilities.
- Don't put `realDevice`, `name` or `build` under `appium:` — they're
  TestingBot's, so they go in `tb:options`.
- Don't re-upload an unchanged binary on every CI job.
- Don't pin an exact device model when a pattern will do.
- Don't hardcode credentials. Env vars, always.
