import json
from pathlib import Path

import pytest

from shortfall import doctables

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def data():
    return doctables.Data(ROOT)


def text(doc: str) -> str:
    return (ROOT / doc).read_text(encoding="utf-8")


def test_every_results_table_matches_the_committed_data(data):
    assert doctables.problems(ROOT, d=data) == []


@pytest.mark.parametrize(
    "doc,old,new",
    [
        ("RESULTS.md", "| 9 of 10, median 110 |", "| 9 of 10, median 111 |"),
        ("README.md", "| 23 of 30 runs |", "| 24 of 30 runs |"),
        ("README.md", "| 7 of 10 | 9 of 10 | 10 of 10 |", "| 6 of 10 | 9 of 10 | 10 of 10 |"),
        ("RESULTS.md", "| 9 of 10, median 23 |", "| 9 of 10, median 24 |"),
        ("RESULTS.md", "| 0.02 | 0.16 |", "| 0.03 | 0.16 |"),
        ("RESULTS.md", "| 2980 | 0 |", "| 2981 | 0 |"),
        ("RESULTS.md", "| 0 of 3 | 2 of 3 | 0 of 3 |", "| 1 of 3 | 2 of 3 | 0 of 3 |"),
        ("RESULTS.md", "| 0.45% |", "| 0.40% |"),
        ("benchmark/README.md", "| 298 | 3 of 3 | 144 |", "| 297 | 3 of 3 | 144 |"),
        (
            "benchmark/agent/README.md",
            "| 7 of 10, median 33 | 9 of 10",
            "| 6 of 10, median 33 | 9 of 10",
        ),
    ],
)
def test_a_changed_number_is_caught(data, doc, old, new):
    body = text(doc)
    assert body.count(old) >= 1
    found = doctables.problems(ROOT, {doc: body.replace(old, new, 1)}, data)
    assert len(found) == 1 and found[0].startswith(doc)
    assert f"the doc says {new.strip('| ').split(' | ')[0]!r}" in found[0]


def test_a_dropped_row_is_caught(data):
    body = text("RESULTS.md")
    row = next(x for x in body.splitlines() if x.startswith("| Grid | 10 |"))
    found = doctables.problems(ROOT, {"RESULTS.md": body.replace(row + "\n", "")}, data)
    assert found == [
        "RESULTS.md '| Method | Trials | Median runs used |': 4 rows, the data gives 5"
    ]


def test_a_new_table_must_be_checked(data):
    body = text("RESULTS.md") + "\n| Something | New |\n|---|---|\n| 1 | 2 |\n"
    found = doctables.problems(ROOT, {"RESULTS.md": body}, data)
    assert found == ["RESULTS.md: the table '| Something | New |' is not checked"]


def test_a_missing_table_is_caught(data):
    body = text("README.md")
    start = body.index("| Test scenario | Public bug |")
    end = body.index("\n\n", start)
    found = doctables.problems(ROOT, {"README.md": body[:start] + body[end + 2 :]}, data)
    assert found == [
        "README.md: no table starting "
        "'| Test scenario | Public bug | Rule broken on plain Medusa |'"
    ]


@pytest.mark.parametrize(
    "old,new,said",
    [
        ("39 of Shortfall's", "38 of Shortfall's", "38"),
        ("16,994 committed runs", "16,993 committed runs", "16,993"),
        ("and all 39 are marked", "and all 38 are marked", "38"),
        ("In every one of them Oversold", "In 38 of them Oversold", "38"),
    ],
)
def test_a_changed_unknown_outcome_count_is_caught(data, old, new, said):
    body = text("RESULTS.md")
    assert body.count(old) == 1
    found = doctables.problems(ROOT, {"RESULTS.md": body.replace(old, new)}, data)
    assert len(found) == 1 and f"the doc says {said!r}" in found[0]


def test_a_missing_unknown_outcome_line_is_caught(data):
    body = text("RESULTS.md").replace("committed runs had a checkout", "runs had a call")
    found = doctables.problems(ROOT, {"RESULTS.md": body}, data)
    assert len(found) == 1 and found[0].startswith("RESULTS.md: no line matching")


def test_unknown_outcome_runs_are_counted_and_all_marked_inconclusive(tmp_path):
    folder = tmp_path / "benchmark" / "x" / "runs" / "set"
    folder.mkdir(parents=True)
    verdicts = [{"check": c, "version": 1, "result": "pass"} for c in doctables.CHECKS]
    ops = [{"phase": "race", "step": "complete_cart", "cart": "a", "outcome": "unknown"}]
    (folder / "run-001.json").write_text(json.dumps({"verdicts": verdicts, "operations": ops}))
    (folder / "run-002.json").write_text(json.dumps({"verdicts": verdicts, "operations": []}))
    d = doctables.Data.__new__(doctables.Data)
    d.root, d._unknown = tmp_path, None
    assert d.unknown_runs() == {"runs": 2, "unknown": 1, "inconclusive": 1, "oversold_pass": 1}
