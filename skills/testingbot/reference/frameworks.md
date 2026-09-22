# Framework connection snippets

Connection only. For Playwright, use the `testingbot-playwright` skill — it
covers a lot more than this.

If the MCP server is installed, `setupTestingBot` detects the framework in the
user's project and returns the matching snippet. Prefer that over these.

## Selenium — JavaScript

```javascript
const { Builder } = require('selenium-webdriver');

const driver = await new Builder()
  .usingServer(`https://${process.env.TESTINGBOT_KEY}:${process.env.TESTINGBOT_SECRET}@hub.testingbot.com/wd/hub`)
  .withCapabilities({
    browserName: 'chrome',
    browserVersion: 'latest',
    platformName: 'Windows 11',
    'tb:options': { name: 'My Test', build: 'build-1' },
  })
  .build();
```

## Selenium — Python

```python
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.browser_version = "latest"
options.platform_name = "Windows 11"
options.set_capability("tb:options", {"name": "My Test", "build": "build-1"})

driver = webdriver.Remote(
    command_executor=f"https://{os.environ['TESTINGBOT_KEY']}:{os.environ['TESTINGBOT_SECRET']}@hub.testingbot.com/wd/hub",
    options=options,
)
```

## Selenium — Java

```java
ChromeOptions options = new ChromeOptions();
options.setBrowserVersion("latest");
options.setPlatformName("Windows 11");
options.setCapability("tb:options", Map.of("name", "My Test", "build", "build-1"));

WebDriver driver = new RemoteWebDriver(
    new URL(String.format("https://%s:%s@hub.testingbot.com/wd/hub",
        System.getenv("TESTINGBOT_KEY"), System.getenv("TESTINGBOT_SECRET"))),
    options);
```

## Selenium — C#

```csharp
var options = new ChromeOptions {
    BrowserVersion = "latest",
    PlatformName = "Windows 11",
};
options.AddAdditionalOption("tb:options", new Dictionary<string, object> {
    { "name", "My Test" }, { "build", "build-1" },
});

var uri = new Uri($"https://{key}:{secret}@hub.testingbot.com/wd/hub");
IWebDriver driver = new RemoteWebDriver(uri, options.ToCapabilities());
```

## WebdriverIO

Use the service — it reports pass/fail and sets the session name for you.

```bash
npm install --save-dev @wdio/testingbot-service
```

```javascript
// wdio.conf.js
exports.config = {
  user: process.env.TESTINGBOT_KEY,
  key: process.env.TESTINGBOT_SECRET,
  hostname: 'hub.testingbot.com',
  port: 443,
  path: '/wd/hub',
  protocol: 'https',
  services: ['testingbot'],
  capabilities: [
    { browserName: 'chrome', browserVersion: 'latest', platformName: 'Windows 11' },
  ],
};
```

## Nightwatch

```bash
npm install nightwatch testingbot-api --save-dev
```

```javascript
// nightwatch.conf.js
const testingBotOptions = {
  'tb:options': {
    build: 'nightwatch-example',
    name: 'Nightwatch Example Test',
    key: process.env.TESTINGBOT_KEY,
    secret: process.env.TESTINGBOT_SECRET,
  },
};

const testingBot = {
  webdriver: {
    start_process: false,
    host: 'hub.testingbot.com',
    port: 443,
    default_path_prefix: '/wd/hub',
    ssl: true,
    keep_alive: true,
    timeout_options: { timeout: 120000, retry_attempts: 3 },
  },
  desiredCapabilities: {
    browserName: 'chrome',
    ...testingBotOptions,
  },
};

module.exports = {
  src_folders: ['tests'],
  custom_commands_path: 'custom_commands',
  test_settings: {
    default: { launch_url: 'https://testingbot.com' },
    'testingbot.chrome': { ...testingBot },
  },
};
```

Nightwatch doesn't report pass/fail on its own. Add a custom command that calls
`updateTest` from the `testingbot-api` package and invoke it in `afterEach`:

```javascript
// custom_commands/customTestingBotEnd.js
exports.command = function (callback) {
  const TestingBot = require('testingbot-api');
  const tb = new TestingBot({
    api_key: process.env.TESTINGBOT_KEY,
    api_secret: process.env.TESTINGBOT_SECRET,
  });

  const jobName = this.currentTest.name;
  const passed = this.currentTest.results.testcases[jobName].failed === 0;

  tb.updateTest({ 'test[success]': passed, 'test[name]': jobName },
    this.sessionId, () => this.end(callback));
};
```

## Puppeteer

Connect with `puppeteer-core`, not `puppeteer` — you don't want a bundled
Chromium download for a remote session.

```javascript
const puppeteer = require('puppeteer-core');

const browser = await puppeteer.connect({
  browserWSEndpoint: `wss://cloud.testingbot.com/puppeteer?key=${process.env.TESTINGBOT_KEY}&secret=${process.env.TESTINGBOT_SECRET}&browserName=chrome&browserVersion=latest`,
});
```

## Cypress

Cypress can't point at a remote hub; TestingBot runs the whole suite instead.

```bash
npm install -g testingbot-cypress-cli
testingbot-cypress run --key "$TESTINGBOT_KEY" --secret "$TESTINGBOT_SECRET"
```

Configuration lives in `testingbot.json` alongside `cypress.config.js`. See
https://testingbot.com/support/cypress.

## Appium

Same hub URL as Selenium. The app under test is uploaded first (`uploadFile`,
or `POST /storage`), which returns an `app_url` to pass as the `app`
capability.

```javascript
const { remote } = require('webdriverio');

const driver = await remote({
  hostname: 'hub.testingbot.com',
  port: 443,
  protocol: 'https',
  path: '/wd/hub',
  user: process.env.TESTINGBOT_KEY,
  key: process.env.TESTINGBOT_SECRET,
  capabilities: {
    platformName: 'Android',
    'appium:deviceName': 'Pixel 9',
    'appium:platformVersion': '16.0',
    'appium:automationName': 'UiAutomator2',   // XCUITest for iOS
    'appium:app': 'tb://YOUR_APP_ID',          // or a public https:// URL
    'tb:options': { name: 'Login flow', build: 'build-1', realDevice: true },
  },
});
```

`realDevice: true` selects a physical handset over an emulator/simulator.
`appium:deviceName` accepts a pattern (`"iPhone.*"`), which avoids queueing on
one exact model.

## Espresso, XCUITest, Maestro

Not client-side frameworks — TestingBot runs the suite. Driven entirely through
MCP tools or the REST API; see [mcp-tools.md](mcp-tools.md).
