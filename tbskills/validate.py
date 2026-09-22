"""Structural validation for the skills repo.

Kept importable so the rules can be unit-tested against synthetic fixtures
rather than only against the real skills.
"""

from __future__ import annotations

import json
import pathlib
import re
from dataclasses import dataclass, field

MAX_DESCRIPTION = 1024
MIN_DESCRIPTION = 80
MAX_SKILL_LINES = 500
MIN_EVAL_CASES = 5

EVAL_FIELDS = ("id", "category", "query", "expected_behavior")

_FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n", re.S)
_KEY = re.compile(r"^(\w[\w-]*):(.*)$")
_LINK = re.compile(r"\]\((?!https?://|#)([^)]+)\)")
_FENCE = re.compile(r"^```([\w-]*)\n(.*?)^```", re.M | re.S)


@dataclass
class Report:
    """Collected findings. Errors fail the build; warnings do not."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def parse_frontmatter(text: str) -> dict[str, str] | None:
    """Parse the leading YAML block.

    Deliberately minimal — the frontmatter we use is flat strings plus folded
    block scalars, so a real YAML parser would only add a dependency.
    Returns None when there is no frontmatter at all.
    """
    match = _FRONTMATTER.match(text)
    if not match:
        return None

    fields: dict[str, str] = {}
    key: str | None = None
    for line in match.group(1).split("\n"):
        keyed = _KEY.match(line)
        if keyed:
            key = keyed.group(1)
            fields[key] = keyed.group(2).strip()
        elif key and line.strip():
            fields[key] = f"{fields[key]} {line.strip()}".strip()
    return {k: v.lstrip("> |").strip() for k, v in fields.items()}


def iter_links(text: str):
    """Yield relative link targets, stripped of any anchor."""
    for target in _LINK.findall(text):
        target = target.split("#")[0].strip()
        if target:
            yield target


def iter_code_blocks(text: str):
    """Yield (language, body) for every fenced block."""
    for language, body in _FENCE.findall(text):
        yield language.lower(), body


def _check_skill(skill_md: pathlib.Path, root: pathlib.Path, report: Report) -> None:
    rel = skill_md.relative_to(root)
    skill_dir = skill_md.parent
    text = skill_md.read_text()

    fields = parse_frontmatter(text)
    if fields is None:
        report.error(f"{rel}: missing YAML frontmatter")
        return

    name = fields.get("name", "")
    if not name:
        report.error(f"{rel}: frontmatter has no 'name'")
    elif name != skill_dir.name:
        report.error(f"{rel}: name '{name}' != directory '{skill_dir.name}'")

    description = fields.get("description", "")
    if not description:
        report.error(f"{rel}: frontmatter has no 'description'")
    elif len(description) > MAX_DESCRIPTION:
        report.error(f"{rel}: description is {len(description)} chars (max {MAX_DESCRIPTION})")
    elif len(description) < MIN_DESCRIPTION:
        report.warn(f"{rel}: description is short ({len(description)} chars) — weak triggering")

    lines = text.count("\n")
    if lines > MAX_SKILL_LINES:
        report.warn(f"{rel}: {lines} lines — move detail into reference/")

    for target in iter_links(text):
        if not (skill_dir / target).exists():
            report.error(f"{rel}: broken link -> {target}")

    eval_file = root / "evals" / f"{skill_dir.name}-evals.json"
    if not eval_file.exists():
        report.error(f"{rel}: no eval suite at evals/{eval_file.name}")


def _check_reference_reachable(ref: pathlib.Path, root: pathlib.Path, report: Report) -> None:
    skill_dir = ref.parent.parent
    needle = f"reference/{ref.name}"
    siblings = [skill_dir / "SKILL.md", *skill_dir.glob("reference/*.md")]
    for page in siblings:
        if page != ref and needle in page.read_text():
            return
    report.warn(f"{ref.relative_to(root)}: never linked — unreachable")


def _check_evals(eval_file: pathlib.Path, root: pathlib.Path, report: Report) -> None:
    rel = eval_file.relative_to(root)
    try:
        data = json.loads(eval_file.read_text())
    except json.JSONDecodeError as exc:
        report.error(f"{rel}: invalid JSON — {exc}")
        return

    cases = data.get("evals", [])
    if len(cases) < MIN_EVAL_CASES:
        report.warn(f"{rel}: only {len(cases)} cases")

    seen: set[str] = set()
    for case in cases:
        for name in EVAL_FIELDS:
            if not case.get(name):
                report.error(f"{rel}: case {case.get('id', '?')} missing '{name}'")
        case_id = case.get("id")
        if case_id in seen:
            report.error(f"{rel}: duplicate id '{case_id}'")
        seen.add(case_id)


def validate_repo(root: pathlib.Path) -> Report:
    """Validate every skill, reference page and eval suite under ``root``."""
    report = Report()
    skills = root / "skills"

    for skill_md in sorted(skills.glob("*/SKILL.md")):
        _check_skill(skill_md, root, report)
    for ref in sorted(skills.glob("*/reference/*.md")):
        _check_reference_reachable(ref, root, report)
    for eval_file in sorted((root / "evals").glob("*.json")):
        _check_evals(eval_file, root, report)

    return report
