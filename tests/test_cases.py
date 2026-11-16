import re
import shutil
from pathlib import Path

import pytest
import yaml

from shortfall.cases import Control, load_case

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
    assert lines.scoring == Control(
        kind="variant",
        file="pr-16961-control.yaml",
        role="scoring",
        variant="pr-16961",
        version="2.22.0",
    )
    assert len(lines.controls) == 1
    assert lines.notes.endswith(
        "#16961, a community pull request for #16502 that was closed without being merged."
    )
    assert "#17436 (opened 2026-10-22)" in lines.notes
    counter = load_case(CASES / "medusa-17032-counter")
    assert counter.rule == "reserved_matches_reservations"
    for case in ("medusa-17032-counter", "medusa-17032-last-unit"):
        loaded = load_case(CASES / case)
        assert [(c.file, c.kind, c.role, c.variant, c.version) for c in loaded.controls] == [
            ("pr-17420-control.yaml", "variant", "scoring", "pr-17420", "2.22.0"),
            ("redis-control.yaml", "redis-locking", "cross-check", None, None),
            ("one-server-control.yaml", "one-server", "history", None, None),
        ]
        assert loaded.scoring.variant == "pr-17420"
        assert "in the open issue #16569." in loaded.notes
        assert loaded.notes.endswith(
            "pr-17420 is Medusa 2.22.0 with the change from medusajs/medusa#17420, a community "
            "pull request that was closed without being merged."
        )


def good_data() -> dict:
    return yaml.safe_load((GOOD / "case.yaml").read_text(encoding="utf-8"))


def write_case(tmp_path: Path, data: dict, name: str = "medusa-17032-last-unit") -> Path:
    folder = tmp_path / name
    folder.mkdir()
    for source in GOOD.glob("*.yaml"):
        if source.name != "case.yaml":
            shutil.copy(source, folder / source.name)
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
        lambda d: set_path(d["controls"][0], "extra", 1),
        "unknown field controls[0].extra",
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
    ("controls missing", lambda d: del_path(d, "controls"), "controls is required"),
    ("controls empty", lambda d: set_path(d, "controls", []), "one or more controls"),
    ("controls not list", lambda d: set_path(d, "controls", {"kind": "variant"}), "controls must"),
    ("control not mapping", lambda d: set_path(d, "controls", ["x"]), "controls[0] must be"),
    (
        "control kind",
        lambda d: set_path(d["controls"][1], "kind", "fixed-version"),
        "controls[1].kind must be one of",
    ),
    (
        "control role",
        lambda d: set_path(d["controls"][1], "role", "main"),
        "controls[1].role must be one of",
    ),
    (
        "control file missing",
        lambda d: set_path(d["controls"][1], "file", "nope.yaml"),
        "controls[1].file",
    ),
    (
        "control file path",
        lambda d: set_path(d["controls"][1], "file", "../redis-control.yaml"),
        "controls[1].file",
    ),
    (
        "no scoring control",
        lambda d: set_path(d["controls"][0], "role", "cross-check"),
        "exactly one scoring control, got 0",
    ),
    (
        "two scoring controls",
        lambda d: set_path(d["controls"][1], "role", "scoring"),
        "exactly one scoring control, got 2",
    ),
    (
        "repeated control file",
        lambda d: set_path(d["controls"][2], "file", "redis-control.yaml"),
        "must not repeat a file",
    ),
    (
        "variant without variant",
        lambda d: del_path(d["controls"][0], "variant"),
        "controls[0].variant must be",
    ),
    (
        "variant without version",
        lambda d: del_path(d["controls"][0], "version"),
        "controls[0].version must be",
    ),
    (
        "variant on a version the case does not run",
        lambda d: set_path(d["controls"][0], "version", "2.18.0"),
        "must be one of the case's versions",
    ),
    (
        "variant name form",
        lambda d: set_path(d["controls"][0], "variant", "PR 17420"),
        "controls[0].variant must be a kebab-case",
    ),
    (
        "variant field without variant kind",
        lambda d: set_path(d["controls"][1], "variant", "pr-17420"),
        "controls[1].variant is only allowed with kind variant",
    ),
    (
        "version without variant kind",
        lambda d: set_path(d["controls"][2], "version", "2.22.0"),
        "controls[2].version is only allowed with kind variant",
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


def test_agent_sees_leaves_out_history_and_coding_guides():
    for folder in sorted(p for p in CASES.iterdir() if p.is_dir()):
        case = load_case(folder)
        for items in (case.agent_sees.guided, case.agent_sees.unguided):
            assert (
                "the Medusa source code for the case's version, without git history, changelogs, "
                "changesets or guides written for AI coding tools"
            ) in items


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


def test_every_case_note_is_read_in_full():
    for folder in sorted(p for p in CASES.iterdir() if p.is_dir()):
        case = load_case(folder)
        text = (folder / "case.yaml").read_text(encoding="utf-8")
        if case.notes:
            assert case.notes in text
            assert case.notes.endswith(".")


VARIANTS = CASES.parent.parent / ".oversold" / "targets" / "medusa" / "variants"


@pytest.mark.skipif(not VARIANTS.is_dir(), reason="needs the pinned Oversold clone")
def test_variant_controls_name_a_variant_at_the_pin():
    found = 0
    for folder in sorted(p for p in CASES.iterdir() if p.is_dir()):
        for control in load_case(folder).controls:
            if control.kind != "variant":
                continue
            spec = yaml.safe_load((VARIANTS / control.variant / "variant.yaml").read_text())
            assert spec["name"] == control.variant
            assert spec["base_version"] == control.version
            found += 1
    assert found == 3
