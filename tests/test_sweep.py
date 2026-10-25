import ast
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from shortfall import sweep
from shortfall.cases import strict_load
from shortfall.control import one_server

ROOT = Path(__file__).resolve().parent.parent
OVERSOLD = ROOT / ".oversold" / "bin" / "oversold"
TOP = {
    "schema",
    "name",
    "description",
    "target",
    "stock",
    "carts",
    "race",
    "timing",
    "faults",
    "runs",
    "seed",
}
KEBAB = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")


def files(candidates, out: Path) -> list[tuple[str, bytes]]:
    return [(p.name, p.read_bytes()) for p in sweep.write(candidates, out)]


def test_grid_same_seed_same_files(tmp_path):
    a = files(sweep.grid(0), tmp_path / "a")
    b = files(sweep.grid(0), tmp_path / "b")
    assert a == b
    assert len(a) == 40


def test_grid_different_seed_different_files(tmp_path):
    a = files(sweep.grid(0), tmp_path / "a")
    b = files(sweep.grid(1), tmp_path / "b")
    assert [n for n, _ in a] == [n for n, _ in b]
    assert all(x != y for (_, x), (_, y) in zip(a, b, strict=True))


def test_random_same_seed_same_files(tmp_path):
    a = files(sweep.random_candidates(5, 30), tmp_path / "a")
    b = files(sweep.random_candidates(5, 30), tmp_path / "b")
    assert a == b


def test_random_different_seed_different_files(tmp_path):
    a = files(sweep.random_candidates(5, 30), tmp_path / "a")
    b = files(sweep.random_candidates(6, 30), tmp_path / "b")
    assert [x for _, x in a] != [x for _, x in b]


def test_grid_order_is_stated():
    names = [c.name for c in sweep.grid(0)]
    assert names[0] == "grid-001-s2-solo-c2-under-together"
    assert names[17] == "grid-018-s2-piece-twopack-c10-ample-together"
    assert names[18] == "grid-019-s1-solo-c2-under-together"
    assert names[35] == "grid-036-s1-piece-twopack-c10-ample-together"
    assert names[36:] == [
        "grid-037-s2-solo-c2-short-sequential",
        "grid-038-s2-piece-twopack-c2-short-sequential",
        "grid-039-s1-solo-c2-short-sequential",
        "grid-040-s1-piece-twopack-c2-short-sequential",
    ]


def test_grid_stock_levels():
    by_name = {c.name: c for c in sweep.grid(0)}
    assert dict(by_name["grid-001-s2-solo-c2-under-together"].stock) == {"SOLO": 0}
    assert dict(by_name["grid-002-s2-solo-c2-short-together"].stock) == {"SOLO": 1}
    assert dict(by_name["grid-003-s2-solo-c2-ample-together"].stock) == {"SOLO": 20}
    assert dict(by_name["grid-013-s2-piece-twopack-c2-under-together"].stock) == {"WIDGET": 2}
    assert dict(by_name["grid-017-s2-piece-twopack-c10-short-together"].stock) == {"WIDGET": 27}


def all_candidate_sets():
    return [sweep.grid(0), sweep.random_candidates(1, 60), sweep.random_candidates(2, 60)]


def check_scenario(data: dict) -> None:
    assert set(data) == TOP
    assert data["schema"] == "oversold.scenario/v1"
    assert KEBAB.fullmatch(data["name"]) and len(data["name"]) <= sweep.MAX_NAME
    assert data["description"].strip()
    assert data["target"] == {
        "engine": "medusa",
        "version": "2.21.2",
        "servers": data["target"]["servers"],
    }
    servers = data["target"]["servers"]
    assert servers in (1, 2)
    assert data["faults"] == []
    assert data["timing"]["release"] in ("together", "sequential")
    assert set(data["timing"]) == {"release"}
    assert data["carts"]
    actions = 0
    counts = {}
    for name, cart in data["carts"].items():
        assert KEBAB.fullmatch(name)
        assert set(cart) <= {"server", "count", "lines"}
        assert 1 <= cart["server"] <= servers
        assert 1 <= cart.get("count", 1) <= 100
        counts[name] = cart.get("count", 1)
        skus = [line["sku"] for line in cart["lines"]]
        assert skus and len(skus) == len(set(skus))
        for line in cart["lines"]:
            assert set(line) == {"sku", "qty"}
            assert line["sku"] in sweep.SKUS
            assert 1 <= line["qty"] <= 1000
    for key, value in data["stock"].items():
        assert key in ("WIDGET", "SOLO")
        assert 0 <= value <= 1000000
    ids = [a["id"] for a in data["race"]]
    assert len(ids) == len(set(ids))
    for action in data["race"]:
        assert set(action) == {"id", "server", "do", "cart"}
        assert action["do"] == "complete"
        assert action["cart"] in data["carts"]
        assert 1 <= action["server"] <= servers
        actions += counts[action["cart"]]
    assert actions <= 200
    assert 1 <= data["runs"] <= 1000
    assert isinstance(data["seed"], int)


def test_every_generated_file_passes_the_strict_loader(tmp_path):
    paths = []
    for i, candidates in enumerate(all_candidate_sets()):
        paths += sweep.write(candidates, tmp_path / f"c{i}")
    assert len(paths) == 160
    for path in paths:
        text = path.read_text(encoding="utf-8")
        data = strict_load(text)
        check_scenario(data)
        if data["target"]["servers"] == 2:
            control = strict_load(one_server(text))
            check_scenario(control)
            assert control["target"]["servers"] == 1


@pytest.mark.skipif(not OVERSOLD.exists(), reason="needs the pinned Oversold binary, make oversold")
def test_every_generated_file_passes_oversold_validate(tmp_path):
    out = ROOT / "runs" / f"pytest-validate-{tmp_path.name}"
    try:
        paths = sweep.write(sweep.grid(0) + sweep.random_candidates(3, 20), out)
        controls = []
        for p in paths:
            text = p.read_text(encoding="utf-8")
            if strict_load(text)["target"]["servers"] == 2:
                c = p.with_name(f"{p.stem}-control.yaml")
                c.write_text(one_server(text), encoding="utf-8")
                controls.append(c)
        for p in paths + controls:
            proc = subprocess.run(
                ["sh", "scripts/oversold.sh", "validate", str(p)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            assert proc.returncode == 0, proc.stdout + proc.stderr
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_write_refuses_a_folder_that_is_not_empty(tmp_path):
    (tmp_path / "x").mkdir()
    (tmp_path / "x" / "keep").write_text("1")
    with pytest.raises(ValueError, match="not empty"):
        sweep.write(sweep.grid(0), tmp_path / "x")


def test_sweep_knows_nothing_about_the_cases():
    source = Path(sweep.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    top = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            top |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            top.add(node.module)
    assert top == {"argparse", "datetime", "random", "re", "sys", "dataclasses", "pathlib", "yaml"}
    for word in ("benchmark", "reference", "load_case", "case_map", "17032", "16502"):
        assert word not in source
