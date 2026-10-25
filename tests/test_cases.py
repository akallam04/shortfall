import re
import shutil
from pathlib import Path

import pytest
import yaml

from shortfall.cases import load_case

CASES = Path(__file__).resolve().parent.parent / "benchmark" / "cases"
GOOD = CASES / "medusa-17032-last-unit"


def test_real_cases_load():
    ids = sorted(p.name for p in CASES.iterdir() if p.is_dir())
    assert ids == ["medusa-16502-lines", "medusa-17032-counter", "medusa-17032-last-unit"]
    for case_id in ids:
        case = load_case(CASES / case_id)
        assert case.id == case_id
        assert case.versions == ("2.21.2", "2.19.0", "2.22.0")


def test_real_case_fields():
    lines = load_case(CASES / "medusa-16502-lines")
    assert lines.control.kind == "none"
    assert lines.control.reason
    assert lines.notes
    counter = load_case(CASES / "medusa-17032-counter")
    assert counter.rule == "reserved_matches_reservations"
    assert counter.control.kind == "one-server"
    assert counter.control.version is None


def good_data() -> dict:
    return yaml.safe_load((GOOD / "case.yaml").read_text(encoding="utf-8"))


def write_case(tmp_path: Path, data: dict, name: str = "medusa-17032-last-unit") -> Path:
    folder = tmp_path / name
    folder.mkdir()
    shutil.copy(GOOD / "reference.yaml", folder / "reference.yaml")
    (folder / "case.yaml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return folder


def test_good_copy_loads(tmp_path):
    assert load_case(write_case(tmp_path, good_data())).id == "medusa-17032-last-unit"


def set_path(data, path, value):
    keys = path.split(".")
    for k in keys[:-1]:
        data = data[k]
    data[keys[-1]] = value


def del_path(data, path):
    keys = path.split(".")
    for k in keys[:-1]:
        data = data[k]
    del data[keys[-1]]


BAD = [
    ("unknown top field", lambda d: set_path(d, "extra", 1), "unknown field extra"),
    ("unknown nested field", lambda d: set_path(d, "issue.extra", 1), "unknown field issue.extra"),
    (
        "unknown control field",
        lambda d: set_path(d, "control.extra", 1),
        "unknown field control.extra",
    ),
    (
        "unknown reference field",
        lambda d: set_path(d, "reference.extra", 1),
        "unknown field reference.extra",
    ),
    (
        "unknown agent_sees field",
        lambda d: set_path(d, "agent_sees.extra", []),
        "unknown field agent_sees.extra",
    ),
    ("schema", lambda d: set_path(d, "schema", "shortfall.case/v2"), "schema"),
    ("missing schema", lambda d: del_path(d, "schema"), "schema is required"),
    ("id not kebab", lambda d: set_path(d, "id", "Medusa_17032"), "kebab-case"),
    ("id not folder", lambda d: set_path(d, "id", "medusa-other"), "folder name"),
    ("empty title", lambda d: set_path(d, "title", "  "), "title"),
    ("title not text", lambda d: set_path(d, "title", 5), "title"),
    ("engine", lambda d: set_path(d, "engine", "saleor"), "engine"),
    ("versions empty", lambda d: set_path(d, "versions", []), "versions"),
    ("versions not list", lambda d: set_path(d, "versions", "2.21.2"), "versions"),
    ("version form", lambda d: set_path(d, "versions", ["2.21"]), "versions[0]"),
    ("version v prefix", lambda d: set_path(d, "versions", ["v2.21.2"]), "versions[0]"),
    ("version repeated", lambda d: set_path(d, "versions", ["2.21.2", "2.21.2"]), "repeat"),
    ("issue missing", lambda d: del_path(d, "issue"), "issue is required"),
    (
        "issue url pull",
        lambda d: set_path(d, "issue.url", "https://github.com/medusajs/medusa/pull/17032"),
        "issue.url",
    ),
    (
        "issue url host",
        lambda d: set_path(d, "issue.url", "https://gitlab.com/medusajs/medusa/issues/1"),
        "issue.url",
    ),
    ("issue opened text", lambda d: set_path(d, "issue.opened", "last week"), "issue.opened"),
    ("issue opened bad day", lambda d: set_path(d, "issue.opened", "2026-02-30"), "issue.opened"),
    ("issue state empty", lambda d: set_path(d, "issue.state", ""), "issue.state"),
    ("rule", lambda d: set_path(d, "rule", "no_double_charge"), "rule"),
    ("control kind", lambda d: set_path(d, "control.kind", "two-server"), "control.kind"),
    ("control kind missing", lambda d: del_path(d, "control.kind"), "control.kind is required"),
    (
        "fixed-version without version",
        lambda d: set_path(d, "control.kind", "fixed-version"),
        "control.version is required",
    ),
    (
        "version without fixed-version",
        lambda d: set_path(d, "control.version", "2.19.0"),
        "control.version is only allowed",
    ),
    (
        "none without reason",
        lambda d: set_path(d, "control.kind", "none"),
        "control.reason is required",
    ),
    (
        "reason without none",
        lambda d: set_path(d, "control.reason", "because"),
        "control.reason is only allowed",
    ),
    (
        "reference file missing",
        lambda d: set_path(d, "reference.file", "nope.yaml"),
        "reference.file",
    ),
    (
        "reference file path",
        lambda d: set_path(d, "reference.file", "../reference.yaml"),
        "reference.file",
    ),
    ("reference source empty", lambda d: set_path(d, "reference.source", ""), "reference.source"),
    ("guided empty", lambda d: set_path(d, "agent_sees.guided", []), "agent_sees.guided"),
    ("unguided missing", lambda d: del_path(d, "agent_sees.unguided"), "agent_sees.unguided"),
    ("unguided item", lambda d: set_path(d, "agent_sees.unguided", [""]), "agent_sees.unguided[0]"),
    ("notes empty", lambda d: set_path(d, "notes", ""), "notes"),
]


@pytest.mark.parametrize("change,expected", [(b[1], b[2]) for b in BAD], ids=[b[0] for b in BAD])
def test_bad_case_raises(tmp_path, change, expected):
    data = good_data()
    change(data)
    with pytest.raises(ValueError, match=re.escape(expected)):
        load_case(write_case(tmp_path, data))


def test_fixed_version_with_version_loads(tmp_path):
    data = good_data()
    data["control"] = {"kind": "fixed-version", "version": "2.22.0"}
    assert load_case(write_case(tmp_path, data)).control.version == "2.22.0"


def test_lists_every_problem(tmp_path):
    data = good_data()
    data["rule"] = "nope"
    data["engine"] = "nope"
    data["extra"] = 1
    with pytest.raises(ValueError) as err:
        load_case(write_case(tmp_path, data))
    message = str(err.value)
    assert "rule" in message and "engine" in message and "unknown field extra" in message


def test_duplicate_key_raises(tmp_path):
    folder = write_case(tmp_path, good_data())
    text = (folder / "case.yaml").read_text(encoding="utf-8")
    (folder / "case.yaml").write_text(text + "rule: no_oversell\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate key"):
        load_case(folder)


def test_missing_case_file(tmp_path):
    with pytest.raises(ValueError, match="cannot read"):
        load_case(tmp_path)


def test_not_a_mapping(tmp_path):
    folder = write_case(tmp_path, good_data())
    (folder / "case.yaml").write_text("- a\n- b\n", encoding="utf-8")
    with pytest.raises(ValueError, match="must be a mapping"):
        load_case(folder)
