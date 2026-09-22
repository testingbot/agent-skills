# Capabilities

TestingBot is W3C WebDriver compliant: standard keys go at the top level,
everything TestingBot-specific goes inside `tb:options`.

```javascript
{
  browserName: 'chrome',
  browserVersion: 'latest',
  platformName: 'Windows 11',
  'tb:options': {
    name: 'Checkout flow',
    build: 'ci-1042',
    screenrecorder: true
  }
}
```

Putting TestingBot keys at the top level is the most common mistake — a strict
W3C endpoint rejects unknown top-level keys.

## Always set these

| Key | Why |
|---|---|
| `name` | The session label in the dashboard. Use the test name. |
| `build` | Groups a parallel run into one build. Use the CI run ID (`GITHUB_RUN_ID`, `BUILD_NUMBER`). Without it, parallel sessions scatter. |

## Session behaviour

| Key | Default | Notes |
|---|---|---|
| `screenrecorder` | `true` | Video. Disable for large parallel runs — recording adds per-session overhead. |
| `screenshot` | `false` | Automatic screenshot capture. |
| `recordLogs` | `true` | Also accepts `strip-parameters` to keep GET/POST params off the test page — use it when URLs carry tokens. |
| `public` | `false` | Makes results viewable without login. Only when the user asks. |
| `timeZone` | `Etc/UTC` | Location name (`Europe/Brussels`), not a path. |
| `screen-resolution` | `1280x1024` | Allowed values differ between Windows/Linux and macOS. |
| `blacklist` | — | Comma-separated hostnames redirected to localhost. Handy for killing analytics/beacons in tests. |
| `geoCountryCode` | — | Two-letter country code for geolocation testing. |
| `tunnelIdentifier` | — | Bind the session to a named tunnel. See [tunnel.md](tunnel.md). |
| `maxDuration` | — | Seconds before the session is killed. Raise it for long suites, lower it to stop runaway sessions burning minutes. |
| `idletimeout` | — | Seconds of inactivity before the session is reaped. |
| `realDevice` | `false` | Mobile: physical handset instead of emulator/simulator. |
| `deviceName` | — | Mobile: model, or a regex like `"iPhone.*"`. |

## Driver version pinning

`seleniumVersion` (also accepted as `selenium-version`), `chromedriverVersion`,
`geckodriverVersion`, `edgedriverVersion`, `iedriverVersion`,
`operaDriverVersion`.

Leave these unset. TestingBot picks a compatible driver, and a pinned version
is a future breakage. Set one only to reproduce a specific failure, and leave a
comment saying why.

## Prerun

`prerun` takes an `https://` or `tb://` URL to an executable fetched and run on
the VM before the test. `prerun-args` passes arguments, `prerun-wait` controls
whether the session waits for it to finish.

Use for installing a certificate or setting a registry key. Don't use it as a
general setup hook — it is slow and hard to debug.

## Device allocation (mobile)

| Key | Notes |
|---|---|
| `deviceName` | Accepts regex/wildcards: `"iPhone.*"` matches any available iPhone. Prefer a pattern over an exact model — exact models queue when busy. |
| `version` | Device OS version. |
| `phoneOnly` / `tabletOnly` | Restrict form factor. |

Confirm a device exists with `getDevices` before naming one exactly.

## Tunnel

Route a session through a running tunnel with the tunnel's identifier. See
[tunnel.md](tunnel.md) — when you start the tunnel locally and point the driver
at `http://localhost:4445/wd/hub`, no capability change is needed at all.

## Playwright and Puppeteer

Same `tb:options` object, delivered differently: the whole capabilities object
is JSON-encoded into a `capabilities` query parameter on the WebSocket URL, and
`key`/`secret` go inside `tb:options` rather than in a Basic-auth URL. Platform
is `platform` (or `platformName`) — there is no `os` key. See the
`testingbot-playwright` skill.
