"""Functional tests over the real skill content.

These encode the facts a model gets wrong about TestingBot. A failure here
usually means a skill would teach an assistant something untrue.
"""

import json
import pathlib
import re

import pytest
import yaml

from tbskills import iter_code_blocks, parse_frontmatter, validate_repo

ALLOWED_HOSTS = {
    "testingbot.com",
    "hub.testingbot.com",
    "cloud.testingbot.com",
    "api.testingbot.com",
}

URL = re.compile(r"(?:https?|wss)://([a-zA-Z0-9.-]*testingbot\.com)")

ENV_VARS = re.compile(r"\b(TESTINGBOT_[A-Z_]+|TB_[A-Z_]+)\b")
ALLOWED_ENV_VARS = {
    "TESTINGBOT_KEY",
    "TESTINGBOT_SECRET",
    "TESTINGBOT_USERNAME",
    "TESTINGBOT_ACCESS_KEY",
    "TESTINGBOT_PROFILE",
    "TESTINGBOT_CONFIG_DIR",
    "TB_KEY",
    "TB_SECRET",
    "TB_CLOUD",
}

SECRET_SHAPED = re.compile(r"\b[a-f0-9]{32}\b")


class TestStructure:
    def test_repo_validates_without_errors(self, root):
        report = validate_repo(root)
        assert report.ok, "\n".join(report.errors)

    def test_every_skill_is_listed_in_the_readme(self, root, skill_dirs):
        readme = (root / "README.md").read_text()
        missing = [d.name for d in skill_dirs if f"`{d.name}`" not in readme]
        assert not missing, f"not documented in README: {missing}"

    def test_plugin_manifest_is_valid(self, root):
        manifest = json.loads((root / ".claude-plugin/plugin.json").read_text())
        assert manifest["name"] == "testingbot"
        assert manifest["mcpServers"]["testingbot"]["args"][-1].startswith("@testingbot/mcp-server")

    def test_marketplace_lists_the_plugin(self, root):
        market = json.loads((root / ".claude-plugin/marketplace.json").read_text())
        assert [p["name"] for p in market["plugins"]] == ["testingbot"]

    def test_frontmatter_declares_name_and_description(self, skill_dirs):
        for skill in skill_dirs:
            fields = parse_frontmatter((skill / "SKILL.md").read_text())
            assert fields, f"{skill.name}: no frontmatter"
            assert fields["name"] == skill.name
            assert len(fields["description"]) >= 80


class TestCodeBlocks:
    def test_json_blocks_parse(self, markdown_files):
        for path in markdown_files:
            for language, body in iter_code_blocks(path.read_text()):
                if language == "json":
                    json.loads(body)

    def test_yaml_blocks_parse(self, markdown_files):
        for path in markdown_files:
            for language, body in iter_code_blocks(path.read_text()):
                # Indented fragments are snippets to splice into a larger file;
                # only whole documents are parseable on their own.
                if language in {"yaml", "yml"} and not body.startswith(" "):
                    yaml.safe_load(body)

    def test_xml_blocks_are_balanced(self, markdown_files):
        import xml.etree.ElementTree as ET

        for path in markdown_files:
            for language, body in iter_code_blocks(path.read_text()):
                if language == "xml":
                    ET.fromstring(body)


class TestFactualInvariants:
    """The corrections that cost real digging. Locked so they can't regress."""

    def test_playwright_never_uses_the_nonexistent_os_capability(self, root):
        for path in (root / "skills/testingbot-playwright").rglob("*.md"):
            for _, body in iter_code_blocks(path.read_text()):
                assert not re.search(r"^\s*os:", body, re.M), (
                    f"{path.name}: 'os' is not a TestingBot parameter; use 'platform'"
                )

    def test_playwright_uses_the_capabilities_query_parameter(self, root):
        skill = (root / "skills/testingbot-playwright/SKILL.md").read_text()
        assert "capabilities=${encodeURIComponent(JSON.stringify(capabilities))}" in skill

    def test_playwright_status_uses_testingbot_executor(self, root):
        skill = (root / "skills/testingbot-playwright/SKILL.md").read_text()
        assert "testingbot_executor" in skill
        assert "setSessionStatus" in skill
        assert "tb:test-result" not in skill, "that is the WebDriver mechanism, not Playwright's"

    def test_selenium_status_uses_the_javascript_executor(self, root):
        skill = (root / "skills/testingbot-selenium/SKILL.md").read_text()
        assert "tb:test-result=" in skill
        assert "testingbot_executor" not in skill, "that is the CDP mechanism, not WebDriver's"

    def test_appium_capabilities_carry_the_vendor_prefix(self, root):
        for path in (root / "skills/testingbot-appium").rglob("*.md"):
            for _, body in iter_code_blocks(path.read_text()):
                for key in ("deviceName", "platformVersion", "automationName"):
                    for line in body.splitlines():
                        if re.search(rf"[\"']?{key}[\"']?\s*[:=]", line):
                            assert "appium:" in line or "set" in line or "." in line, (
                                f"{path.name}: '{key}' needs the appium: prefix — {line.strip()}"
                            )

    def test_appium_keeps_testingbot_keys_out_of_the_appium_namespace(self, root):
        for path in (root / "skills/testingbot-appium").rglob("*.md"):
            text = path.read_text()
            for key in ("realDevice", "appiumVersion"):
                assert f"appium:{key}" not in text, f"{path.name}: {key} belongs in tb:options"

    def test_hub_url_is_the_wd_hub_endpoint(self, markdown_files):
        # Capture only URL-path characters; surrounding syntax varies by language.
        hub_path = re.compile(r"hub\.testingbot\.com([\w/.-]*)")
        for path in markdown_files:
            for match in hub_path.finditer(path.read_text()):
                tail = match.group(1).rstrip(".")
                assert tail in {"", "/wd/hub"}, f"{path.name}: unexpected hub path {tail!r}"


class TestSafety:
    def test_only_known_testingbot_hosts_appear(self, markdown_files):
        for path in markdown_files:
            for host in URL.findall(path.read_text()):
                assert host in ALLOWED_HOSTS, f"{path.name}: unknown host {host}"

    def test_only_documented_env_vars_appear(self, markdown_files):
        for path in markdown_files:
            for name in ENV_VARS.findall(path.read_text()):
                assert name in ALLOWED_ENV_VARS, f"{path.name}: undocumented env var {name}"

    def test_no_secret_shaped_literals(self, markdown_files):
        for path in markdown_files:
            found = SECRET_SHAPED.findall(path.read_text())
            assert not found, f"{path.name}: looks like a real key/app id: {found}"

    def test_credentials_are_never_literals_in_examples(self, markdown_files):
        bad = re.compile(r"""(key|secret)["']?\s*[:=]\s*["'](?!YOUR_|api_|\$|\{)[a-zA-Z0-9]{8,}["']""")
        for path in markdown_files:
            for _, body in iter_code_blocks(path.read_text()):
                hits = bad.findall(body)
                assert not hits, f"{path.name}: hardcoded credential in an example"


class TestEvals:
    def test_suite_name_matches_filename(self, root):
        for path in sorted((root / "evals").glob("*.json")):
            data = json.loads(path.read_text())
            assert data["skill"] == path.name.replace("-evals.json", "")

    def test_every_skill_has_a_suite(self, root, skill_dirs):
        for skill in skill_dirs:
            assert (root / "evals" / f"{skill.name}-evals.json").exists()

    def test_case_ids_are_globally_unique(self, root):
        seen: dict[str, str] = {}
        for path in sorted((root / "evals").glob("*.json")):
            for case in json.loads(path.read_text())["evals"]:
                assert case["id"] not in seen, (
                    f"{case['id']} in both {seen.get(case['id'])} and {path.name}"
                )
                seen[case["id"]] = path.name

    def test_expected_behaviours_are_non_empty_strings(self, root):
        for path in sorted((root / "evals").glob("*.json")):
            for case in json.loads(path.read_text())["evals"]:
                assert case["expected_behavior"], f"{case['id']}: no expectations"
                for behaviour in case["expected_behavior"]:
                    assert isinstance(behaviour, str) and behaviour.strip()

    def test_each_suite_guards_against_over_triggering(self, root):
        """A skill that fires on unrelated work is worse than no skill."""
        for path in sorted((root / "evals").glob("*.json")):
            cases = json.loads(path.read_text())["evals"]
            negative = [
                c for c in cases
                if any(
                    phrase in b.lower()
                    for c2 in [c] for b in c2["expected_behavior"]
                    for phrase in ("does not", "does NOT".lower(), "never")
                )
            ]
            assert negative, f"{path.name}: no case asserting what must NOT happen"


class TestNoPlaceholders:
    def test_no_unfinished_markers(self, markdown_files):
        for path in markdown_files:
            text = path.read_text()
            for marker in ("TODO", "FIXME", "XXX", "lorem ipsum"):
                assert marker not in text, f"{path.name}: contains {marker}"
