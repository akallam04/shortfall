import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from shortfall.cases import load_case
from shortfall.control import main, one_server, redis_locking

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "benchmark" / "cases"
LAST_UNIT = CASES / "medusa-17032-last-unit" / "reference.yaml"
DATA = Path(__file__).resolve().parent / "data"


def server_fields(data):
    fields = [data["target"]["servers"]]
    fields += [cart["server"] for cart in data["carts"].values()]
    fields += [action["server"] for action in data["race"]]
    return fields


def without(data, keys):
    data = yaml.safe_load(yaml.safe_dump(data))
    for key in keys:
        data.pop(key, None)
    data["target"].pop("servers")
    for cart in data["carts"].values():
        cart.pop("server")
    for action in data["race"]:
        action.pop("server")
    return data


def test_last_unit_control_servers():
    text = LAST_UNIT.read_text(encoding="utf-8")
    before = yaml.safe_load(text)
    after = yaml.safe_load(one_server(text))
    assert set(server_fields(before)) == {1, 2}
    assert set(server_fields(after)) == {1}
    assert after["name"] == "last-unit-two-servers-control"
    assert (
        after["description"]
        == "One-server control of last-unit-two-servers. " + before["description"]
    )
    assert without(after, ["name", "description"]) == without(before, ["name", "description"])
    assert list(after) == list(before)


def test_last_unit_control_matches_oversold_one_server():
    after = yaml.safe_load(one_server(LAST_UNIT.read_text(encoding="utf-8")))
    oversold = yaml.safe_load((DATA / "last-unit-one-server.yaml").read_text(encoding="utf-8"))
    differ = sorted(k for k in set(after) | set(oversold) if after.get(k) != oversold.get(k))
    assert differ == ["description", "name", "seed"]


def test_one_server_scenario_raises():
    with pytest.raises(ValueError, match="target.servers 2"):
        one_server((DATA / "last-unit-one-server.yaml").read_text(encoding="utf-8"))


def test_long_name_raises():
    data = yaml.safe_load(LAST_UNIT.read_text(encoding="utf-8"))
    data["name"] = "a" * 57
    with pytest.raises(ValueError, match="over 64"):
        one_server(yaml.safe_dump(data, sort_keys=False))
    data["name"] = "a" * 56
    assert yaml.safe_load(one_server(yaml.safe_dump(data, sort_keys=False)))["name"] == (
        "a" * 56 + "-control"
    )


@pytest.mark.parametrize("case_id", sorted(p.parent.name for p in CASES.glob("*/control.yaml")))
def test_committed_control_matches_generator(case_id):
    folder = CASES / case_id
    out = subprocess.run(
        [sys.executable, "-m", "shortfall.control", str(folder / "reference.yaml")],
        check=True,
        capture_output=True,
    ).stdout
    assert out == (folder / "control.yaml").read_bytes()


def test_one_server_controls_are_kept_for_the_17032_cases():
    assert sorted(p.parent.name for p in CASES.glob("*/control.yaml")) == [
        "medusa-17032-counter",
        "medusa-17032-last-unit",
    ]


REDIS = {
    "medusa-17032-last-unit": "last-unit-two-servers-redis-locking.yaml",
    "medusa-17032-counter": "counter-two-servers-redis-locking.yaml",
}


@pytest.mark.parametrize("case_id", sorted(REDIS))
def test_redis_rewrite_matches_oversold_redis_locking_scenario(case_id):
    text = (CASES / case_id / "reference.yaml").read_text(encoding="utf-8")
    before = yaml.safe_load(text)
    after = yaml.safe_load(redis_locking(text))
    oversold = yaml.safe_load((DATA / REDIS[case_id]).read_text(encoding="utf-8"))
    differ = sorted(k for k in set(after) | set(oversold) if after.get(k) != oversold.get(k))
    assert differ == ["description", "name"]
    assert list(after) == list(oversold) == list(before)
    assert list(after["target"]) == list(oversold["target"]) == [*before["target"], "locking"]
    assert after["target"]["locking"] == "redis"
    assert after["name"] == before["name"] + "-redis-control"
    assert after["description"] == (
        f"Redis-locking control of {before['name']}. " + before["description"]
    )
    rest = {k: v for k, v in after.items() if k not in ("name", "description", "target")}
    assert rest == {k: v for k, v in before.items() if k not in ("name", "description", "target")}


def test_redis_rewrite_refuses_a_redis_scenario():
    text = (DATA / REDIS["medusa-17032-last-unit"]).read_text(encoding="utf-8")
    with pytest.raises(ValueError, match="already uses target.locking: redis"):
        redis_locking(text)


def test_redis_rewrite_keeps_an_explicit_in_memory_field_in_place():
    data = yaml.safe_load(LAST_UNIT.read_text(encoding="utf-8"))
    data["target"] = {"engine": "medusa", "locking": "in-memory", "version": "2.21.2", "servers": 2}
    after = yaml.safe_load(redis_locking(yaml.safe_dump(data, sort_keys=False)))
    assert list(after["target"]) == ["engine", "locking", "version", "servers"]
    assert after["target"]["locking"] == "redis"


def test_redis_long_name_raises():
    data = yaml.safe_load(LAST_UNIT.read_text(encoding="utf-8"))
    data["name"] = "a" * 51
    with pytest.raises(ValueError, match="over 64"):
        redis_locking(yaml.safe_dump(data, sort_keys=False))
    data["name"] = "a" * 50
    assert yaml.safe_load(redis_locking(yaml.safe_dump(data, sort_keys=False)))["name"] == (
        "a" * 50 + "-redis-control"
    )


def test_redis_rewrite_works_on_one_server_scenarios():
    text = (DATA / "last-unit-one-server.yaml").read_text(encoding="utf-8")
    after = yaml.safe_load(redis_locking(text))
    assert after["target"]["servers"] == 1
    assert after["target"]["locking"] == "redis"


REDIS_CASES = sorted(
    p.name for p in CASES.iterdir() if p.is_dir() and load_case(p).control.kind == "redis-locking"
)


def test_the_17032_cases_use_redis_locking_controls():
    assert REDIS_CASES == ["medusa-17032-counter", "medusa-17032-last-unit"]


@pytest.mark.parametrize("case_id", REDIS_CASES)
def test_committed_redis_control_matches_generator(case_id):
    folder = CASES / case_id
    out = subprocess.run(
        [
            sys.executable,
            "-m",
            "shortfall.control",
            "--redis-locking",
            str(folder / "reference.yaml"),
        ],
        check=True,
        capture_output=True,
    ).stdout
    assert out == (folder / "redis-control.yaml").read_bytes()


@pytest.mark.parametrize("argv", [[], ["--redis-locking"], ["--other", "x.yaml"], ["a", "b"]])
def test_bad_command_lines(argv, capsys):
    assert main(argv) == 2
    assert "usage:" in capsys.readouterr().err
