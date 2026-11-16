from pathlib import Path

import pytest

from shortfall.answers import (
    ACCEPTED,
    NOT_ACCEPTED,
    NOT_APPLICABLE,
    grade,
    load_answer,
    located,
)

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "benchmark" / "cases"
SNAPSHOT = ROOT / "snapshots" / "medusa-2.22.0"
INVENTORY = "packages/modules/inventory/src/services/inventory-module.ts"
CONFIRM = "packages/core/core-flows/src/cart/steps/confirm-inventory.ts"
RESERVE = "packages/core/core-flows/src/cart/steps/reserve-inventory.ts"
IN_MEMORY = "packages/modules/locking/src/providers/in-memory.ts"


def test_answer_keys():
    assert load_answer(CASES / "medusa-16502-lines") == (INVENTORY, CONFIRM)
    for case in ("medusa-17032-last-unit", "medusa-17032-counter"):
        assert load_answer(CASES / case) == (INVENTORY, RESERVE, IN_MEMORY)
    assert sorted(p.parent.name for p in CASES.glob("*/answer.yaml")) == sorted(
        p.name for p in CASES.iterdir() if p.is_dir()
    )


@pytest.mark.skipif(not SNAPSHOT.is_dir(), reason="needs snapshots/medusa-2.22.0")
def test_every_answer_path_exists_in_the_2_22_0_snapshot():
    for folder in sorted(CASES.glob("*/answer.yaml")):
        for path in load_answer(folder.parent):
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
def test_grading_is_by_exact_path(named, expected):
    assert grade(CASES / "medusa-16502-lines", named) == expected


def test_located_result():
    cases = {p.name: p for p in CASES.iterdir() if p.is_dir()}
    assert located(cases, ["medusa-17032-last-unit"], None) == {"result": NOT_APPLICABLE}
    assert located(cases, ["medusa-17032-last-unit", "medusa-16502-lines"], RESERVE) == {
        "result": "graded",
        "file": RESERVE,
        "cases": {"medusa-17032-last-unit": ACCEPTED, "medusa-16502-lines": NOT_ACCEPTED},
    }
    assert located(cases, [], IN_MEMORY) == {"result": "graded", "file": IN_MEMORY, "cases": {}}


@pytest.mark.parametrize(
    "text,message",
    [
        ("schema: x\ncase: medusa-x\nfiles: [packages/a.ts]\n", "schema must be"),
        ("schema: shortfall.answer/v1\ncase: other\nfiles: [packages/a.ts]\n", "case must be"),
        ("schema: shortfall.answer/v1\ncase: medusa-x\nfiles: []\n", "one or more"),
        ("schema: shortfall.answer/v1\ncase: medusa-x\nfiles: [/packages/a.ts]\n", "files[0]"),
        ("schema: shortfall.answer/v1\ncase: medusa-x\nfiles: [packages/../a.ts]\n", "files[0]"),
        ("schema: shortfall.answer/v1\ncase: medusa-x\nfiles: [src/a.ts]\n", "files[0]"),
        (
            "schema: shortfall.answer/v1\ncase: medusa-x\nfiles: [packages/a.ts, packages/a.ts]\n",
            "repeat",
        ),
        ("schema: shortfall.answer/v1\ncase: medusa-x\nfiles: [packages/a.ts]\nx: 1\n", "unknown"),
    ],
)
def test_bad_answer_files_are_refused(tmp_path, text, message):
    folder = tmp_path / "medusa-x"
    folder.mkdir()
    (folder / "answer.yaml").write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match=message.replace("[", r"\[")):
        load_answer(folder)
