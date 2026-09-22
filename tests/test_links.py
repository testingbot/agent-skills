"""Checks every documented URL still resolves.

Deselected by default — run with `-m network`, and on a schedule in CI. Doc
URLs rot quietly, and a skill that sends an assistant to a 404 is worse than
one that says nothing.
"""

import re
import urllib.error
import urllib.request

import pytest

EXTERNAL = re.compile(r"https://[^\s)>\"'`]+")
TRAILING = "`'\"),.;:"

# Only documentation pages are checked. api.* and hub.* are authenticated
# service endpoints: they answer 401/404 to an anonymous HEAD, which says
# nothing about whether the skills describe them correctly.
DOC_HOST = "testingbot.com"
SKIP_HOSTS = {"api.testingbot.com", "hub.testingbot.com", "cloud.testingbot.com"}


def _urls(markdown_files):
    seen: dict[str, str] = {}
    for path in markdown_files:
        for raw in EXTERNAL.findall(path.read_text()):
            url = raw.rstrip(TRAILING)
            # Interpolated URLs from code samples are templates, not addresses.
            if any(m in url for m in ("${", "#{", "{", "[", "YOUR_", "@")):
                continue
            host = url.split("/")[2]
            if host in SKIP_HOSTS or not host.endswith(DOC_HOST):
                continue
            seen.setdefault(url, path.name)
    return sorted(seen.items())


@pytest.mark.network
def test_documented_urls_resolve(markdown_files):
    broken = []
    for url, source in _urls(markdown_files):
        request = urllib.request.Request(url, method="HEAD",
                                         headers={"User-Agent": "testingbot-agent-skills/ci"})
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                if response.status >= 400:
                    broken.append(f"{response.status} {url} (in {source})")
        except urllib.error.HTTPError as exc:
            if exc.code == 405:  # HEAD not allowed; the page exists
                continue
            broken.append(f"{exc.code} {url} (in {source})")
        except Exception as exc:  # noqa: BLE001 - report, don't mask
            broken.append(f"{type(exc).__name__} {url} (in {source})")

    assert not broken, "unreachable documented URLs:\n" + "\n".join(broken)
