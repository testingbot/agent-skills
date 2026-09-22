# TestingBot Agent Skills

Agent Skills that teach AI coding assistants — Claude Code, Cursor, Copilot,
Gemini CLI — how to write test automation that runs on
[TestingBot](https://testingbot.com).

Companion to the [TestingBot MCP server](https://github.com/testingbot/mcp-server).
The two do different jobs:

|  | MCP server | Skills |
|---|---|---|
| Job | Act on the account *now* | Write code into the repo |
| Examples | List live devices, fetch failure logs, upload an APK, start a Maestro run | `playwright.config.ts`, capability blocks, CI workflows |
| Needs | Install + auth | Nothing |

An assistant with only the MCP server writes cloud config from memory. An
assistant with only the skills can't see the account. Install both.

## Install

Claude Code — installs the skills *and* wires up the MCP server:

```
/plugin marketplace add testingbot/agent-skills
/plugin install testingbot
```

Any other assistant — copy the skill directories into wherever it reads skills
from (`~/.claude/skills/`, `.cursor/rules/`, …):

```bash
git clone https://github.com/testingbot/agent-skills
cp -r agent-skills/skills/* ~/.claude/skills/
```

Then authenticate. Either ask the assistant to "log me in to TestingBot"
(browser OAuth via the MCP `tb_login` tool, nothing to paste), or:

```bash
export TESTINGBOT_KEY="your-key"
export TESTINGBOT_SECRET="your-secret"
```

## Skills

| Skill | Covers |
|---|---|
| `testingbot` | Umbrella: routing to MCP tools, credentials, capabilities, tunnels, REST API, per-framework connection snippets |
| `testingbot-playwright` | Playwright on the cloud: wss endpoint, cross-browser projects, status reporting, tunnels, CI, debugging cloud-only failures |
| `testingbot-selenium` | Selenium on the cloud in 6 languages: hub URL, W3C capabilities, tb:test-result annotation, session IDs, parallel suites, Grid, CI |
| `testingbot-appium` | Appium for native, hybrid and Flutter apps: app upload, the three capability namespaces, real device vs emulator, permissions, locale, Appium versions |

Each skill is a `SKILL.md` that stays under ~200 lines, with detail in
`reference/*.md` loaded only when the task needs it. Keeping `SKILL.md` short
is deliberate: it is what the assistant reads on every relevant turn.

## What these skills deliberately don't do

They don't teach Playwright, Selenium or Appium. Models already know those
frameworks, and a skill that re-explains `getByRole` is context spent for
nothing. These skills carry only what a model gets *wrong* about TestingBot:
endpoints, capability shapes, which MCP tool answers which question, and the
failure modes specific to running in someone else's browser.

## Contributing

```bash
pip install -r requirements-dev.txt
python3 scripts/validate_skills.py   # structure: frontmatter, links, eval coverage
python3 -m pytest -q                 # unit + functional tests
python3 -m pytest -m network         # optional: every documented URL still resolves
```

All of these run in CI and must pass.

**`tests/test_validate.py`** unit-tests the validator against synthetic
fixtures, so its rules are themselves covered rather than assumed.

**`tests/test_skills.py`** tests the real content. Beyond structure it locks
down the facts that are easy to get wrong and expensive to get wrong:
Playwright uses `platform` and never `os`; Playwright reports status via
`testingbot_executor` while WebDriver uses `tb:test-result`; Appium
capabilities carry the `appium:` prefix and TestingBot's own keys stay in
`tb:options`; only known hosts and documented environment variables appear;
no credential-shaped literals. Each eval suite must also contain at least one
case asserting what the skill must *not* do — over-triggering is the realistic
failure mode once several skills are installed.

**`tests/test_links.py`** is deselected by default and runs weekly. Doc URLs
rot quietly, and a skill that sends an assistant to a 404 is worse than one
that says nothing.

Every skill needs an eval suite in `evals/<skill-name>-evals.json`. Add cases
for anything a skill gets wrong in practice; that is how these stay honest as
the platform changes.

Browser and device tables are deliberately absent from the skill text. They
drift. The skills tell the assistant to call `getBrowsers` / `getDevices`
instead.

## License

MIT
