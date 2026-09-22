"""Unit tests for the validator itself, against synthetic fixtures."""

import json

import pytest
from conftest import make_skill

from tbskills import iter_code_blocks, iter_links, parse_frontmatter, validate_repo


class TestParseFrontmatter:
    def test_returns_none_without_frontmatter(self):
        assert parse_frontmatter("# Just a heading\n") is None

    def test_reads_flat_keys(self):
        fields = parse_frontmatter("---\nname: a\nlicense: MIT\n---\n\nbody")
        assert fields == {"name": "a", "license": "MIT"}

    def test_joins_folded_block_scalar(self):
        text = "---\nname: a\ndescription: >\n  one two\n  three\n---\n\nbody"
        assert parse_frontmatter(text)["description"] == "one two three"

    def test_ignores_body_after_closing_fence(self):
        fields = parse_frontmatter("---\nname: a\n---\n\nname: not-this\n")
        assert fields["name"] == "a"


class TestIterLinks:
    def test_yields_relative_targets(self):
        assert list(iter_links("see [x](reference/x.md)")) == ["reference/x.md"]

    def test_skips_external_and_anchors(self):
        text = "[a](https://x.com) [b](#section) [c](reference/c.md)"
        assert list(iter_links(text)) == ["reference/c.md"]

    def test_strips_anchor_from_relative_link(self):
        assert list(iter_links("[a](reference/a.md#top)")) == ["reference/a.md"]


class TestIterCodeBlocks:
    def test_reads_language_and_body(self):
        blocks = list(iter_code_blocks("```python\nx = 1\n```\n"))
        assert blocks == [("python", "x = 1\n")]

    def test_handles_unlabelled_block(self):
        assert list(iter_code_blocks("```\nplain\n```\n")) == [("", "plain\n")]

    def test_reads_multiple_blocks(self):
        text = "```js\na\n```\ntext\n```json\n{}\n```\n"
        assert [lang for lang, _ in iter_code_blocks(text)] == ["js", "json"]


class TestValidateRepo:
    def test_accepts_a_minimal_valid_skill(self, tmp_path):
        make_skill(tmp_path, "good")
        report = validate_repo(tmp_path)
        assert report.ok, report.errors

    def test_rejects_name_directory_mismatch(self, tmp_path):
        skill = make_skill(tmp_path, "good")
        skill.joinpath("SKILL.md").write_text(
            "---\nname: other\ndescription: %s\n---\n\nbody" % ("x" * 120)
        )
        report = validate_repo(tmp_path)
        assert any("!= directory" in e for e in report.errors)

    def test_rejects_missing_frontmatter(self, tmp_path):
        skill = make_skill(tmp_path, "good")
        skill.joinpath("SKILL.md").write_text("# no frontmatter\n")
        report = validate_repo(tmp_path)
        assert any("missing YAML frontmatter" in e for e in report.errors)

    def test_rejects_broken_relative_link(self, tmp_path):
        make_skill(tmp_path, "good", body="see [x](reference/missing.md)\n")
        report = validate_repo(tmp_path)
        assert any("broken link" in e for e in report.errors)

    def test_accepts_link_that_resolves(self, tmp_path):
        skill = make_skill(tmp_path, "good", body="see [x](reference/x.md)\n")
        skill.joinpath("reference/x.md").write_text("# x\n")
        report = validate_repo(tmp_path)
        assert report.ok, report.errors

    def test_rejects_missing_eval_suite(self, tmp_path):
        make_skill(tmp_path, "good", add_eval=False)
        report = validate_repo(tmp_path)
        assert any("no eval suite" in e for e in report.errors)

    def test_rejects_duplicate_eval_ids(self, tmp_path):
        make_skill(tmp_path, "good")
        path = tmp_path / "evals" / "good-evals.json"
        data = json.loads(path.read_text())
        data["evals"][1]["id"] = data["evals"][0]["id"]
        path.write_text(json.dumps(data))
        report = validate_repo(tmp_path)
        assert any("duplicate id" in e for e in report.errors)

    def test_rejects_eval_case_missing_a_field(self, tmp_path):
        make_skill(tmp_path, "good")
        path = tmp_path / "evals" / "good-evals.json"
        data = json.loads(path.read_text())
        del data["evals"][0]["expected_behavior"]
        path.write_text(json.dumps(data))
        report = validate_repo(tmp_path)
        assert any("missing 'expected_behavior'" in e for e in report.errors)

    def test_rejects_invalid_eval_json(self, tmp_path):
        make_skill(tmp_path, "good")
        (tmp_path / "evals" / "good-evals.json").write_text("{not json")
        report = validate_repo(tmp_path)
        assert any("invalid JSON" in e for e in report.errors)

    @pytest.mark.parametrize("description,expected", [("x" * 40, True), ("x" * 120, False)])
    def test_warns_on_short_description(self, tmp_path, description, expected):
        make_skill(tmp_path, "good", description=description)
        report = validate_repo(tmp_path)
        assert any("description is short" in w for w in report.warnings) is expected
        assert report.ok, report.errors

    def test_warns_on_unreachable_reference_page(self, tmp_path):
        skill = make_skill(tmp_path, "good")
        skill.joinpath("reference/orphan.md").write_text("# orphan\n")
        report = validate_repo(tmp_path)
        assert any("never linked" in w for w in report.warnings)
        assert report.ok, report.errors
