# Appium connection by language

Every example puts credentials in `tb:options` and the app in `appium:app`.
Swap `tb://APP_ID` for a public `https://` URL if the binary is hosted already.

## Java

Use the platform-specific options class — it type-checks the `appium:` keys for
you, which removes the most common source of setup errors.

```java
import io.appium.java_client.ios.IOSDriver;
import io.appium.java_client.ios.options.XCUITestOptions;
import org.openqa.selenium.MutableCapabilities;
import java.net.URL;

XCUITestOptions options = new XCUITestOptions();
options.setPlatformName("iOS");
options.setAutomationName("XCUITest");
options.setDeviceName("iPhone 17");
options.setPlatformVersion("26.0");
options.setApp("tb://YOUR_APP_ID");

MutableCapabilities tbOptions = new MutableCapabilities();
tbOptions.setCapability("key", System.getenv("TESTINGBOT_KEY"));
tbOptions.setCapability("secret", System.getenv("TESTINGBOT_SECRET"));
tbOptions.setCapability("name", "Login flow");
tbOptions.setCapability("realDevice", true);
options.setCapability("tb:options", tbOptions);

IOSDriver driver = new IOSDriver(
    new URL("https://hub.testingbot.com/wd/hub"), options);
```

Android: `UiAutomator2Options` and `AndroidDriver`.

## Python

```python
import os
from appium import webdriver
from appium.options.common import AppiumOptions

capabilities = {
    "platformName": "Android",
    "appium:automationName": "UiAutomator2",
    "appium:deviceName": "Galaxy S24",
    "appium:platformVersion": "14.0",
    "appium:app": "tb://YOUR_APP_ID",
    "tb:options": {
        "key": os.environ["TESTINGBOT_KEY"],
        "secret": os.environ["TESTINGBOT_SECRET"],
        "realDevice": True,
    },
}

options = AppiumOptions().load_capabilities(capabilities)
driver = webdriver.Remote("https://hub.testingbot.com/wd/hub", options=options)
```

`load_capabilities` takes the whole dict, so keep capabilities as data and
build the options object once.

## JavaScript (WebdriverIO)

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
    'appium:automationName': 'UiAutomator2',
    'appium:app': 'tb://YOUR_APP_ID',
    'tb:options': { name: 'Login flow', realDevice: true },
  },
});
```

WebdriverIO takes `user`/`key` at the top of the config, so credentials don't
need to be repeated in `tb:options`.

## C#

```csharp
var options = new AppiumOptions {
    PlatformName = "Android",
    AutomationName = "UiAutomator2",
    App = "tb://YOUR_APP_ID",
};
options.AddAdditionalAppiumOption("appium:deviceName", "Galaxy S24");
options.AddAdditionalAppiumOption("appium:platformVersion", "14.0");
options.AddAdditionalAppiumOption("tb:options", new Dictionary<string, object> {
    ["key"] = Environment.GetEnvironmentVariable("TESTINGBOT_KEY") ?? "",
    ["secret"] = Environment.GetEnvironmentVariable("TESTINGBOT_SECRET") ?? "",
    ["name"] = TestContext.CurrentContext.Test.Name,
    ["realDevice"] = true,
});

var driver = new AndroidDriver(
    new Uri("https://hub.testingbot.com/wd/hub"), options);
```

Report from `[TearDown]` using `TestContext.CurrentContext.Result.Outcome.Status`.
NUnit, SpecFlow and Reqnroll all work the same way.

## Ruby

```ruby
caps = {
  "platformName" => "iOS",
  "appium:automationName" => "XCUITest",
  "appium:deviceName" => "iPhone 17",
  "appium:platformVersion" => "26.0",
  "appium:app" => "tb://YOUR_APP_ID",
  "tb:options" => { "appiumVersion" => "latest" }
}

driver = Appium::Driver.new({
  caps: caps,
  appium_lib: {
    server_url: "https://#{ENV['TESTINGBOT_KEY']}:#{ENV['TESTINGBOT_SECRET']}@hub.testingbot.com/wd/hub"
  }
}, true).start_driver
```

## PHP

```php
$capabilities = [
    'platformName' => 'Android',
    'appium:automationName' => 'UiAutomator2',
    'appium:deviceName' => 'Galaxy S24',
    'appium:app' => 'tb://YOUR_APP_ID',
    'tb:options' => [
        'key' => getenv('TESTINGBOT_KEY'),
        'secret' => getenv('TESTINGBOT_SECRET'),
        'realDevice' => true,
    ],
];

$driver = RemoteWebDriver::create('https://hub.testingbot.com/wd/hub', $capabilities);
```

## Flutter

Appium's Flutter driver needs the app built in **debug or profile mode** —
release builds are not supported, and this is the first thing to check when a
Flutter run fails to connect.

The app must also declare `flutter_driver` in `dev_dependencies` and call
`enableFlutterDriverExtension()` before `runApp` in `main.dart`. That's a change
to the app, not the test — flag it to the user rather than assuming it's done.

Robot Framework and CodeceptJS are supported too; both drive Appium
underneath, so the capabilities above apply unchanged.
