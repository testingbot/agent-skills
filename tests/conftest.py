import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def root() -> pathlib.Path:
    return ROOT


@pytest.fixture(scope="session")
def skill_dirs(root) -> list[pathlib.Path]:
    dirs = sorted(p.parent for p in root.glob("skills/*/SKILL.md"))
    assert dirs, "no skills found"
    return dirs


@pytest.fixture(scope="session")
def markdown_files(root) -> list[pathlib.Path]:
    return sorted(root.glob("skills/**/*.md"))


def make_skill(tmp_path: pathlib.Path, name: str, body: str = "# Body\n",
               description: str = "x" * 120, add_eval: bool = True) -> pathlib.Path:
    """Build a minimal valid skill on disk, for the validator's unit tests."""
    skill_dir = tmp_path / "skills" / name
    (skill_dir / "reference").mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n\n{body}"
    )
    evals = tmp_path / "evals"
    evals.mkdir(exist_ok=True)
    if add_eval:
        (evals / f"{name}-evals.json").write_text(
            '{"skill": "%s", "evals": [%s]}' % (
                name,
                ",".join(
                    '{"id":"c%d","category":"x","query":"q","expected_behavior":["b"]}' % i
                    for i in range(5)
                ),
            )
        )
    return skill_dir
