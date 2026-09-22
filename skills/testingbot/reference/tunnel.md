# Tunnel — testing localhost and internal sites

The cloud browser can't reach `localhost:3000` or a staging host behind a
firewall. The tunnel is an outbound connection from the developer's machine
that the cloud browser routes through.

Check `getTunnelList` first — an already-running tunnel is common and starting
a second one without an identifier causes confusing routing.

## Start it

Java (the reference implementation, requires Java 11+, 17 LTS recommended):

```bash
curl -O https://testingbot.com/downloads/testingbot-tunnel.zip
unzip testingbot-tunnel.zip
java -jar testingbot-tunnel.jar "$TESTINGBOT_KEY" "$TESTINGBOT_SECRET"
```

Wait for `You may start tests` before running anything. Starting tests early
produces a connection error that looks like a test bug.

Node — `testingbot-tunnel-launcher` starts and stops the tunnel from inside a
JS test runner, which is the right shape for `globalSetup` / `globalTeardown`.

Docker — `docker pull testingbot/tunnel`.

GitHub Actions — `testingbot-tunnel-action` as a step, rather than scripting
the JAR by hand.

## Point tests at it

The simplest approach, and the one the docs recommend: change the hub URL.

```
https://hub.testingbot.com/wd/hub   →   http://localhost:4445/wd/hub
```

Nothing else changes. All Selenium, Appium, Playwright and Cypress capabilities
work the same through the tunnel.

For parallel CI jobs that each need their own tunnel, use tunnel identifiers so
sessions bind to the right one — see
https://testingbot.com/support/tunnel/multiple. Flags and env vars are at
https://testingbot.com/support/tunnel/commandline.

## Operational notes

- Outbound only: 443 (HTTPS) and 22 (SSH) to `*.testingbot.com`. A tunnel that
  won't come up on a corporate network is nearly always egress filtering.
- Shutdown: `Ctrl+C`, or `kill -SIGUSR1 <pid>`, then remove
  `~/.testingbot-tunnel.pid` if it is stale.
- Requirements: 4 GB RAM, 2 cores.

## When to suggest one

Suggest a tunnel when the target URL is `localhost`, `127.0.0.1`, a `.local` or
`.internal` host, a private IP range, or a staging host the user describes as
internal. Don't add one by default — it is a process the user has to keep
running, and most tests point at a public URL.
