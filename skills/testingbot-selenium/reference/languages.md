# Selenium connection by language

Every example reads credentials from the environment and puts them in
`tb:options`. Swap in the userinfo hub URL
(`https://KEY:SECRET@hub.testingbot.com/wd/hub`) only if the surrounding code
already does it that way.

## Java

```java
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.remote.RemoteWebDriver;
import java.net.URI;
import java.util.Map;

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

Session ID: `((RemoteWebDriver) driver).getSessionId().toString()`.
API client: `TestingbotREST` — `restApi.updateTest(sessionId, details)` where
`details` carries `name` and `success`.

## Python

```python
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions

options = ChromeOptions()
options.set_capability('platformName', 'WIN11')
options.set_capability('browserVersion', 'latest')
options.set_capability('tb:options', {
    'key': os.environ['TESTINGBOT_KEY'],
    'secret': os.environ['TESTINGBOT_SECRET'],
    'name': 'Checkout flow',
})

driver = webdriver.Remote(
    command_executor='https://hub.testingbot.com/wd/hub',
    options=options,
)
```

In pytest, build the driver in a fixture and report the result on teardown:

```python
import pytest

@pytest.fixture
def driver(request):
    d = make_driver()
    yield d
    passed = request.node.rep_call.passed if hasattr(request.node, 'rep_call') else True
    d.execute_script(f"tb:test-result={'passed' if passed else 'failed'}")
    d.quit()
```

(`rep_call` comes from the standard `pytest_runtest_makereport` hook in
`conftest.py`.)

Session ID: `driver.session_id`. API client: `testingbotclient` —
`tb.tests.update_test(session_id, name=..., passed=True, build=...)`.

## C#

```csharp
var options = new ChromeOptions {
    BrowserVersion = "latest",
    PlatformName = "WIN11",
};
options.AddAdditionalOption("tb:options", new Dictionary<string, object> {
    ["key"] = Environment.GetEnvironmentVariable("TESTINGBOT_KEY") ?? "",
    ["secret"] = Environment.GetEnvironmentVariable("TESTINGBOT_SECRET") ?? "",
    ["name"] = TestContext.CurrentContext.Test.Name,
});

IWebDriver driver = new RemoteWebDriver(
    new Uri("https://hub.testingbot.com/wd/hub"), options.ToCapabilities());
```

In NUnit, report from `[TearDown]` using
`TestContext.CurrentContext.Result.Outcome.Status`.

Session ID: `((RemoteWebDriver)driver).SessionId.ToString()`.

## Ruby

```ruby
require 'selenium-webdriver'

options = Selenium::WebDriver::Chrome::Options.new
options.add_option('platformName', 'WIN11')
options.add_option('browserVersion', 'latest')
options.add_option('tb:options', {
  'key' => ENV['TESTINGBOT_KEY'],
  'secret' => ENV['TESTINGBOT_SECRET'],
  'name' => 'Checkout flow'
})

driver = Selenium::WebDriver.for(:remote,
  url: 'https://hub.testingbot.com/wd/hub',
  options: options)
```

Session ID: `driver.session_id`. API client: the `testingbot` gem —
`api.update_test(session_id, { name: ..., success: true })`.

## JavaScript (selenium-webdriver)

```javascript
const { Builder } = require('selenium-webdriver');

const driver = await new Builder()
  .usingServer(`https://${process.env.TB_KEY}:${process.env.TB_SECRET}@hub.testingbot.com/wd/hub`)
  .withCapabilities({
    browserName: 'chrome',
    browserVersion: 'latest',
    platformName: 'WIN11',
    'tb:options': { name: 'Checkout flow', build: 'build-1' },
  })
  .build();
```

Session ID: `(await driver.getSession()).getId()`. API client: `testingbot-api`
— `api.updateTest({ 'test[success]': '1', 'test[name]': '...' }, sessionId, cb)`.

For WebdriverIO, use `@wdio/testingbot-service` instead — it sets the session
name and reports pass/fail for you. See `reference/frameworks.md` in the
`testingbot` skill.

## PHP

```php
$capabilities = DesiredCapabilities::chrome();
$capabilities->setCapability('platformName', 'WIN11');
$capabilities->setCapability('browserVersion', 'latest');
$capabilities->setCapability('tb:options', [
    'key' => getenv('TESTINGBOT_KEY'),
    'secret' => getenv('TESTINGBOT_SECRET'),
    'name' => 'Checkout flow',
]);

$driver = RemoteWebDriver::create('https://hub.testingbot.com/wd/hub', $capabilities);
```

Session ID: `$driver->getSessionID()`. API client:
`TestingBot\TestingBotAPI` — `$api->updateJob($sessionId, [...])`.
