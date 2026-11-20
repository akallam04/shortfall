import json
import re
import shutil
from pathlib import Path

import pytest
import yaml

from shortfall import agent, freeze, scenario_format
from shortfall.answers import load_causes

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "benchmark" / "cases"
CHECKS_DOC = ROOT / ".oversold" / "docs" / "checks.md"
ISSUES = ROOT / "snapshots" / "issues"


def answer_paths() -> set[str]:
    out = set()
    for answer in CASES.glob("*/answer.yaml"):
        out |= set(yaml.safe_load(answer.read_text())["files"])
    return out


def issue_numbers() -> set[str]:
    out = set()
    for case in CASES.glob("*/case.yaml"):
        out |= set(re.findall(r"\b[0-9]{4,6}\b", case.read_text()))
    return out


NUMBER = re.compile(r"#[0-9]{3,}|issues/[0-9]+|pull/[0-9]+")


def fixed_texts() -> dict[str, str]:
    texts = {p.name: p.read_text(encoding="utf-8") for p in sorted(agent.PROMPTS.glob("*.md"))}
    texts["tools"] = json.dumps(agent.TOOLS)
    texts["feedback"] = json.dumps(agent.FEEDBACK)
    texts["format"] = scenario_format.format_text()
    causes = load_causes(ROOT / "benchmark" / "causes.yaml")
    texts["causes"] = json.dumps(causes)
    if CHECKS_DOC.exists():
        texts["check rules"] = scenario_format.check_rules_text(CHECKS_DOC.read_text())
    return texts


def assert_case_free(name: str, text: str) -> None:
    for path in answer_paths():
        assert path not in text, (name, path)
        assert Path(path).name not in text, (name, path)
    for word in ("answer.yaml", "benchmark/cases", "case.yaml"):
        assert word not in text, (name, word)
    assert not NUMBER.search(text), (name, NUMBER.search(text).group())
    for number in issue_numbers():
        assert number not in text, (name, number)


@pytest.mark.parametrize("name", sorted(fixed_texts()))
def test_no_prompt_or_tool_text_names_a_case(name):
    assert_case_free(name, fixed_texts()[name])


def test_the_scan_finds_what_it_looks_for():
    for bad in (
        "see packages/modules/inventory/src/services/inventory-module.ts",
        "like issue #16502",
        "https://github.com/medusajs/medusa/pull/17420",
    ):
        with pytest.raises(AssertionError):
            assert_case_free("probe", bad)


@pytest.mark.skipif(not (CHECKS_DOC.exists() and ISSUES.exists()), reason="no local snapshots")
def test_the_unguided_opening_names_no_case():
    terms = agent.forbidden_terms(CASES)
    for message in agent.opening(ROOT, "unguided", None, terms):
        assert_case_free(message["role"], message["content"])


@pytest.mark.skipif(not (CHECKS_DOC.exists() and ISSUES.exists()), reason="no local snapshots")
def test_guided_text_names_only_its_own_report_beyond_the_fixed_text():
    terms = agent.forbidden_terms(CASES)
    fixed = agent.opening(ROOT, "unguided", None, terms)[1]["content"]
    for report in sorted(ISSUES.glob("*.md")):
        guided = agent.opening(ROOT, "guided", report.stem, terms)[1]["content"]
        body = report.read_text(encoding="utf-8").strip()
        assert body in guided
        rest = guided.replace(body, "")
        assert_case_free(report.stem, rest)
        assert fixed.split("How the test runs:")[1] in guided


@pytest.mark.skipif(not (CHECKS_DOC.exists() and ISSUES.exists()), reason="no local snapshots")
def test_the_recorded_prompt_hash_is_current():
    assert freeze.recorded_hash(ROOT) == freeze.prompt_hash(ROOT)
    text = (ROOT / freeze.HASH_FILE).read_text()
    for path, _ in freeze.COVERS:
        assert f"- {path}:" in text


def test_the_prompt_hash_moves_with_what_the_model_is_shown(tmp_path, monkeypatch):
    from test_agent import make_root

    root = make_root(tmp_path)
    before = freeze.prompt_hash(root)
    prompts = tmp_path / "prompts"
    shutil.copytree(agent.PROMPTS, prompts)
    monkeypatch.setattr(agent, "PROMPTS", prompts)
    assert freeze.prompt_hash(root) == before
    (prompts / "system.md").write_text("changed\n")
    assert freeze.prompt_hash(root) != before
    monkeypatch.setattr(agent, "KEEP_TURNS", 7)
    changed = freeze.prompt_hash(root)
    monkeypatch.setattr(agent, "KEEP_TURNS", 6)
    assert freeze.prompt_hash(root) != changed


def test_the_variants_hash_differently_and_v2_has_no_variant_key(tmp_path):
    from test_agent import make_root

    root = make_root(tmp_path)
    assert "variant" not in freeze.manifest(root)
    assert freeze.manifest(root, "v2-nomenu")["variant"] == "v2-nomenu"
    assert freeze.prompt_hash(root) != freeze.prompt_hash(root, "v2-nomenu")


@pytest.mark.skipif(not (CHECKS_DOC.exists() and ISSUES.exists()), reason="no local snapshots")
def test_the_recorded_nomenu_hash_is_current():
    assert freeze.recorded_hash(ROOT, "v2-nomenu") == freeze.prompt_hash(ROOT, "v2-nomenu")
    text = (ROOT / freeze.HASH_FILES["v2-nomenu"]).read_text()
    assert "Prompt version v2-nomenu." in text and "causes.yaml" not in text


def test_the_budget_variant_differs_from_v2_only_by_its_gate(tmp_path):
    from test_agent import make_root

    root = make_root(tmp_path)
    v2, budget = freeze.manifest(root), freeze.manifest(root, "v2-budget")
    gate = budget["settings"].pop("finish_gate")
    assert gate == {"runs_left_above": agent.GATE_RUNS, "text": agent.GATE_TEXT}
    assert budget.pop("variant") == "v2-budget"
    assert budget == v2
    assert freeze.prompt_hash(root, "v2-budget") != freeze.prompt_hash(root)


@pytest.mark.skipif(not (CHECKS_DOC.exists() and ISSUES.exists()), reason="no local snapshots")
def test_the_recorded_budget_hash_is_current_and_the_older_ones_did_not_move():
    assert freeze.recorded_hash(ROOT, "v2-budget") == freeze.prompt_hash(ROOT, "v2-budget")
    assert "Prompt version v2-budget." in (ROOT / freeze.HASH_FILES["v2-budget"]).read_text()
    assert freeze.recorded_hash(ROOT) == (
        "14a82a957b7b5b002037f7bde9978b692b1ba3bde93ac54ecc318a00f2b684cb"
    )
    assert freeze.recorded_hash(ROOT, "v2-nomenu") == (
        "47934e6f6c6df629d1e162b2025e896234719b3f05df49182a7d6dbf94050d64"
    )
