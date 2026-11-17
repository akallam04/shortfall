import copy
import subprocess
from pathlib import Path

import pytest
import yaml

from shortfall import scenario_format as sf
from shortfall.score import CandidateRefused, check_candidate

ROOT = Path(__file__).resolve().parent.parent
CHECKS_DOC = ROOT / ".oversold" / "docs" / "checks.md"

FULL = {
    "schema": "oversold.scenario/v1",
    "name": "every-field",
    "description": "Uses every field the format lists.",
    "target": {"engine": "medusa", "version": "2.22.0", "servers": 2},
    "stock": {"WIDGET": 5, "SOLO": 1},
    "stock_before_race": {"WIDGET": 4},
    "carts": {
        "alice": {"server": 1, "count": 2, "lines": [{"sku": "OVS-PIECE", "qty": 1}]},
        "bob": {"server": 2, "lines": [{"sku": "OVS-TWOPACK", "qty": 1}]},
    },
    "race": [
        {"id": "alice-completes", "server": 1, "do": "complete", "cart": "alice"},
        {"id": "bob-completes", "server": 2, "do": "complete", "cart": "bob"},
    ],
    "timing": {"release": "together", "jitter_ms": [0, 5], "request_timeout_ms": 10000},
    "faults": [],
    "runs": 3,
    "seed": 7,
}


def paths(data, prefix=""):
    out = set()
    if isinstance(data, dict):
        for k, v in data.items():
            if prefix == "carts.":
                key = "<name>"
            else:
                key = k
            if isinstance(v, list) and v and isinstance(v[0], dict):
                out.add(f"{prefix}{key}")
                for item in v:
                    out |= paths(item, f"{prefix}{key}[].")
            elif isinstance(v, dict) and k not in ("stock", "stock_before_race"):
                out.add(f"{prefix}{key}")
                out |= paths(v, f"{prefix}{key}.")
            else:
                out.add(f"{prefix}{key}")
    return out


def test_the_full_scenario_uses_every_listed_field():
    listed = {f.path for f in sf.FIELDS}
    used = paths(FULL) - {"target", "timing", "carts.<name>"}
    assert used == listed


def test_every_field_shown_is_accepted():
    check_candidate(copy.deepcopy(FULL))
    check_candidate(copy.deepcopy(sf.EXAMPLE))
    text = sf.format_text()
    for f in sf.FIELDS:
        assert f"| `{f.path}` | {f.type} |" in text


@pytest.mark.skipif(not (ROOT / ".oversold" / "bin" / "oversold").exists(), reason="no Oversold")
def test_oversold_validate_accepts_every_field_shown():
    folder = ROOT / "runs" / "test-format"
    folder.mkdir(parents=True, exist_ok=True)
    for name, data in (("full", FULL), ("example", sf.EXAMPLE)):
        path = folder / f"{name}.yaml"
        path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
        proc = subprocess.run(
            ["sh", "scripts/oversold.sh", "validate", str(path)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr


@pytest.mark.parametrize("field", sorted(sf.REFUSED))
def test_every_refused_field_is_absent_and_refused(field):
    text = sf.format_text()
    assert f"`{field}`" not in text
    assert f"\n{field}:" not in text
    data = copy.deepcopy(FULL)
    if field == "checks":
        data["checks"] = ["no_oversell"]
    else:
        data["target"][field.split(".")[1]] = "x"
    with pytest.raises(CandidateRefused):
        check_candidate(data)


def test_the_format_text_names_no_harness_settings():
    low = sf.format_text().lower()
    for word in ("locking", "redis", "target.variant", "--variant", "checks:"):
        assert word not in low


@pytest.mark.parametrize(
    "change,where",
    [
        (lambda d: d.update(notes="x"), "notes"),
        (lambda d: d["target"].update(region="eu"), "target.region"),
        (lambda d: d["carts"]["alice"].update(email="a@b.c"), "carts.alice.email"),
        (lambda d: d["carts"]["bob"]["lines"][0].update(price=1), "carts.bob.lines[].price"),
        (lambda d: d["race"][0].update(delay=1), "race[].delay"),
        (lambda d: d["timing"].update(settle_ms=1), "timing.settle_ms"),
    ],
)
def test_a_field_outside_the_list_is_refused(change, where):
    data = copy.deepcopy(FULL)
    change(data)
    with pytest.raises(CandidateRefused) as err:
        check_candidate(data)
    assert where in str(err.value)


def test_the_check_rules_text_keeps_the_rules_and_drops_the_rest():
    source = (
        "# Checks\n\nintro\n\nA scenario chooses its checks with the `checks` field.\n\n"
        "## Terms\n\n- term\n\n## Inconclusive runs\n\n1. rule\n\n"
        "## no_oversell (version 2)\n\nrule text\n\n## Known limits\n\n- Redis lock calls\n\n"
        "## Version history\n\n- old\n"
    )
    out = sf.check_rules_text(source)
    assert "## Terms" in out and "## no_oversell (version 2)" in out and "rule text" in out
    for gone in ("`checks` field", "Redis", "Known limits", "Version history", "intro"):
        assert gone not in out
    assert "A scenario cannot choose, skip or change them." in out


@pytest.mark.skipif(not CHECKS_DOC.exists(), reason="no Oversold docs")
def test_the_real_check_rules_text():
    out = sf.check_rules_text(CHECKS_DOC.read_text(encoding="utf-8"))
    for name in sf.CHECK_NAMES:
        assert f"## {name} (version" in out
    low = out.lower()
    for word in ("`checks`", "redis", "locking", "known limits", "version history"):
        assert word not in low
