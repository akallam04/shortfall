from pathlib import Path

import pytest

from shortfall.answers import (
    ACCEPTED,
    NOT_ACCEPTED,
    NOT_APPLICABLE,
    NOT_NAMED,
    Answer,
    fixed_guess,
    grade,
    load_answer,
    load_causes,
    located,
    most_common,
)

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "benchmark" / "cases"
SNAPSHOT = ROOT / "snapshots" / "medusa-2.22.0"
INVENTORY = "packages/modules/inventory/src/services/inventory-module.ts"
CONFIRM = "packages/core/core-flows/src/cart/steps/confirm-inventory.ts"
RESERVE = "packages/core/core-flows/src/cart/steps/reserve-inventory.ts"
IN_MEMORY = "packages/modules/locking/src/providers/in-memory.ts"


CAUSES = (
    "per-line-check",
    "process-local-lock",
    "stale-counter-write",
    "duplicate-completion",
    "payment-order-link",
    "stock-location-mixup",
)
FOLDERS = sorted(p for p in CASES.iterdir() if p.is_dir())


def test_the_cause_list():
    causes = load_causes(CASES.parent / "causes.yaml")
    assert tuple(causes) == CAUSES
    assert all(text.endswith(".") for text in causes.values())


def test_answer_keys():
    assert load_answer(CASES / "medusa-16502-lines") == Answer(
        files=(INVENTORY, CONFIRM), causes=("per-line-check",)
    )
    for case in ("medusa-17032-last-unit", "medusa-17032-counter"):
        assert load_answer(CASES / case) == Answer(
            files=(INVENTORY, RESERVE, IN_MEMORY),
            causes=("process-local-lock", "stale-counter-write"),
        )
    assert sorted(p.parent.name for p in CASES.glob("*/answer.yaml")) == [p.name for p in FOLDERS]
    used = {c for folder in FOLDERS for c in load_answer(folder).causes}
    assert set(CAUSES) - used == {
        "duplicate-completion",
        "payment-order-link",
        "stock-location-mixup",
    }


@pytest.mark.skipif(not SNAPSHOT.is_dir(), reason="needs snapshots/medusa-2.22.0")
def test_every_answer_path_exists_in_the_2_22_0_snapshot():
    for folder in sorted(CASES.glob("*/answer.yaml")):
        for path in load_answer(folder.parent).files:
            assert (SNAPSHOT / path).is_file(), path


@pytest.mark.parametrize(
    "named,expected",
    [
        (CONFIRM, ACCEPTED),
        (INVENTORY, ACCEPTED),
        (RESERVE, NOT_ACCEPTED),
        ("./" + CONFIRM, NOT_ACCEPTED),
        ("/" + CONFIRM, NOT_ACCEPTED),
        (CONFIRM + " ", NOT_ACCEPTED),
        (CONFIRM.upper(), NOT_ACCEPTED),
        (CONFIRM.replace(".ts", ".js"), NOT_ACCEPTED),
        ("confirm-inventory.ts", NOT_ACCEPTED),
    ],
)
def test_files_are_graded_by_exact_path(named, expected):
    assert grade(CASES / "medusa-16502-lines", named, "per-line-check")["file"] == expected


def test_file_cause_and_located_are_graded_separately():
    lines = CASES / "medusa-16502-lines"
    assert grade(lines, CONFIRM, "per-line-check") == dict.fromkeys(
        ("file", "cause", "located"), ACCEPTED
    )
    assert grade(lines, INVENTORY, "process-local-lock") == {
        "file": ACCEPTED,
        "cause": NOT_ACCEPTED,
        "located": NOT_ACCEPTED,
    }
    assert grade(lines, RESERVE, "per-line-check") == {
        "file": NOT_ACCEPTED,
        "cause": ACCEPTED,
        "located": NOT_ACCEPTED,
    }
    assert grade(lines, INVENTORY, None) == {
        "file": ACCEPTED,
        "cause": NOT_NAMED,
        "located": NOT_ACCEPTED,
    }
    assert grade(lines, None, "per-line-check")["located"] == NOT_ACCEPTED


def test_located_result():
    cases = {p.name: p for p in FOLDERS}
    assert located(cases, ["medusa-17032-last-unit"], None, None) == {"result": NOT_APPLICABLE}
    out = located(
        cases, ["medusa-17032-last-unit", "medusa-16502-lines"], RESERVE, "process-local-lock"
    )
    assert out == {
        "result": "graded",
        "file": RESERVE,
        "cause": "process-local-lock",
        "cases": {
            "medusa-17032-last-unit": dict.fromkeys(("file", "cause", "located"), ACCEPTED),
            "medusa-16502-lines": dict.fromkeys(("file", "cause", "located"), NOT_ACCEPTED),
        },
    }
    assert located(cases, [], IN_MEMORY, None) == {
        "result": "graded",
        "file": IN_MEMORY,
        "cause": None,
        "cases": {},
    }


def test_fixed_guesses():
    assert most_common(FOLDERS, "files") == (INVENTORY, 3)
    assert most_common(FOLDERS, "causes") == ("process-local-lock", 2)
    assert fixed_guess(FOLDERS, file=INVENTORY) == {
        "cases": 3,
        "file": 3,
        "cause": 0,
        "located": 0,
    }
    assert fixed_guess(FOLDERS, cause="process-local-lock") == {
        "cases": 3,
        "file": 0,
        "cause": 2,
        "located": 0,
    }
    assert fixed_guess(FOLDERS, file=INVENTORY, cause="process-local-lock") == {
        "cases": 3,
        "file": 3,
        "cause": 2,
        "located": 2,
    }
    assert fixed_guess(FOLDERS, file=INVENTORY, cause="stale-counter-write")["located"] == 2
    assert fixed_guess(FOLDERS, file=INVENTORY, cause="per-line-check")["located"] == 1


@pytest.mark.parametrize(
    "text,message",
    [
        ("schema: x\ncase: medusa-x\nfiles: [packages/a.ts]\n", "schema must be"),
        ("schema: shortfall.answer/v2\ncase: other\nfiles: [packages/a.ts]\n", "case must be"),
        ("schema: shortfall.answer/v2\ncase: medusa-x\nfiles: []\n", "one or more"),
        ("schema: shortfall.answer/v2\ncase: medusa-x\nfiles: [/packages/a.ts]\n", "files[0]"),
        ("schema: shortfall.answer/v2\ncase: medusa-x\nfiles: [packages/../a.ts]\n", "files[0]"),
        ("schema: shortfall.answer/v2\ncase: medusa-x\nfiles: [src/a.ts]\n", "files[0]"),
        (
            "schema: shortfall.answer/v2\ncase: medusa-x\nfiles: [packages/a.ts, packages/a.ts]\n",
            "repeat",
        ),
        (
            "schema: shortfall.answer/v2\ncase: medusa-x\nfiles: [packages/a.ts]\n"
            "causes: [per-line-check]\nx: 1\n",
            "unknown",
        ),
        (
            "schema: shortfall.answer/v2\ncase: medusa-x\nfiles: [packages/a.ts]\n",
            "causes must be a list",
        ),
        (
            "schema: shortfall.answer/v2\ncase: medusa-x\nfiles: [packages/a.ts]\n"
            "causes: [race-condition]\n",
            "causes[0] must be one of",
        ),
        (
            "schema: shortfall.answer/v2\ncase: medusa-x\nfiles: [packages/a.ts]\n"
            "causes: [per-line-check, per-line-check]\n",
            "causes must not repeat",
        ),
    ],
)
def test_bad_answer_files_are_refused(tmp_path, text, message):
    folder = tmp_path / "medusa-x"
    folder.mkdir()
    (folder / "answer.yaml").write_text(text, encoding="utf-8")
    causes = load_causes(CASES.parent / "causes.yaml")
    with pytest.raises(ValueError, match=message.replace("[", r"\[")):
        load_answer(folder, causes)


@pytest.mark.parametrize(
    "text,message",
    [
        ("schema: x\ncauses: [{id: a, description: b}]\n", "schema must be"),
        ("schema: shortfall.causes/v1\ncauses: []\n", "one or more"),
        ("schema: shortfall.causes/v1\ncauses: [{id: A B, description: b}]\n", "kebab-case"),
        ("schema: shortfall.causes/v1\ncauses: [{id: a}]\n", "exactly an id"),
        (
            "schema: shortfall.causes/v1\n"
            "causes: [{id: a, description: b}, {id: a, description: c}]\n",
            "repeats",
        ),
    ],
)
def test_bad_cause_lists_are_refused(tmp_path, text, message):
    path = tmp_path / "causes.yaml"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        load_causes(path)
