# Appium capabilities on TestingBot

Three namespaces. Put each key in the right one — this is where most setup
failures come from.

| Namespace | Owns | Examples |
|---|---|---|
| bare | W3C standard | `platformName` |
| `appium:` | Appium | `deviceName`, `platformVersion`, `automationName`, `app`, `locale`, `orientation`, `autoGrantPermissions` |
| `tb:options` | TestingBot | `key`, `secret`, `name`, `build`, `realDevice`, `appiumVersion` |

Appium 2 and 3 reject unprefixed vendor capabilities outright, so a bare
`deviceName` fails the session rather than being ignored.

## Device selection

| Key | Notes |
|---|---|
| `appium:deviceName` | Model name, or a regex: `"iPhone.*"`, `"Galaxy S.*"`. Patterns avoid queueing behind a busy handset. |
| `appium:platformVersion` | OS version. Omit to take whatever the matched device runs. |
| `tb:options.realDevice` | `true` for physical hardware, otherwise emulator/simulator. |
| `appium:automationName` | `UiAutomator2` (Android), `XCUITest` (iOS). Flutter apps use the Flutter driver. |

`getDevices` reports what exists and what's currently available. Use it instead
of naming models from memory — the fleet changes.

## App under test

| Key | Notes |
|---|---|
| `appium:app` | `tb://APP_ID` from an upload, or a public `https://` URL to an `.apk`/`.ipa`. |

Upload with the MCP `uploadFile` tool, or
`POST https://api.testingbot.com/v1/storage` with `-F "file=@app.apk"`, which
returns `{"app_url":"tb://..."}`.

Install a second app, or a new version, during a test:

```javascript
await driver.execute('mobile: installApp', { appPath: 'tb://<file-id>' });
```

That's the mechanism for app-upgrade tests: install the old build, exercise it,
install the new one, check state survived.

## Appium version

`tb:options.appiumVersion` accepts `latest`, `latest-1`, or an explicit version
such as `3.2.2`.

Leave it unset. TestingBot picks a working version; a pin is a future breakage.
Set it only to reproduce a specific failure, with a comment saying why.

Moving 2.x → 3: Appium 3 removed deprecated endpoints and prefixes
security-flagged commands — `adb_shell` is now `uiautomator2:adb_shell`. A
suite that used those needs edits, so don't bump a pinned version silently.

## Device state

| Key | Value |
|---|---|
| `appium:autoGrantPermissions` | `true` — accepts permission dialogs automatically. Usually what you want; a blocked dialog stalls everything after it. |
| `appium:locale` | Android: two-letter region, `ES`. iOS: language_region, `es_ES`. The formats differ — using the Android form on iOS silently does nothing. |
| `appium:orientation` | `"LANDSCAPE"` or `"PORTRAIT"`. |

## Session metadata

| Key | Notes |
|---|---|
| `tb:options.name` | Session label. Use the test name. |
| `tb:options.build` | Groups a parallel run. Use the CI run ID. |

The rest of `tb:options` — video, logs, timezone, tunnel, geolocation — is in
`reference/capabilities.md` of the `testingbot` skill and applies here too.

## App instrumentation

Some interactions need extra hooks added to the app build:

- **Biometrics** — Face ID / Touch ID prompts in tests
- **Incoming calls and SMS** — emulated, to see how the app responds
- **Camera image injection** — supply a base64 image to the virtual camera
  (Android emulators only)

These need setup on the app side, so they're a conversation with the user, not
a capability you can just add. See
https://testingbot.com/support/app-automate/appium/instrumentation.
