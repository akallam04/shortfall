import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from shortfall.control import one_server

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


def test_controls_exist_for_one_server_cases():
    assert sorted(p.parent.name for p in CASES.glob("*/control.yaml")) == [
        "medusa-17032-counter",
        "medusa-17032-last-unit",
    ]
