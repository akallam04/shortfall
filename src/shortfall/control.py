import re
import sys

import yaml

MAX_NAME = 64
USAGE = (
    "usage: python -m shortfall.control "
    "[--redis-locking | --variant <name> <version>] <scenario.yaml>"
)
_VARIANT = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
_VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")


def _load(text: str) -> dict:
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError("scenario must be a mapping")
    return data


def _rename(data: dict, suffix: str, label: str, detail: str = "") -> None:
    name = data.get("name")
    if not isinstance(name, str) or not name:
        raise ValueError("scenario must have a name")
    control_name = f"{name}-{suffix}"
    if len(control_name) > MAX_NAME:
        raise ValueError(f"control name {control_name!r} is over {MAX_NAME} characters")
    data["name"] = control_name
    description = data.get("description")
    prefix = f"{label} control of {name}{detail}. "
    data["description"] = prefix + description if isinstance(description, str) else prefix.strip()


def _dump(data: dict) -> str:
    return yaml.safe_dump(
        data, sort_keys=False, default_flow_style=False, allow_unicode=True, width=80
    )


def one_server(text: str) -> str:
    data = _load(text)
    target = data.get("target")
    if (
        not isinstance(target, dict)
        or target.get("servers") != 2
        or type(target["servers"]) is not int
    ):
        raise ValueError(
            "scenario must have target.servers 2, a one-server scenario has no one-server control"
        )
    _rename(data, "control", "One-server")
    target["servers"] = 1
    carts = data.get("carts")
    if isinstance(carts, dict):
        for cart in carts.values():
            if isinstance(cart, dict) and "server" in cart:
                cart["server"] = 1
    race = data.get("race")
    if isinstance(race, list):
        for action in race:
            if isinstance(action, dict) and "server" in action:
                action["server"] = 1
    return _dump(data)


def redis_locking(text: str) -> str:
    data = _load(text)
    target = data.get("target")
    if not isinstance(target, dict):
        raise ValueError("scenario must have a target")
    if target.get("locking") == "redis":
        raise ValueError(
            "scenario already uses target.locking: redis, it has no Redis-locking control"
        )
    _rename(data, "redis-control", "Redis-locking")
    target["locking"] = "redis"
    return _dump(data)


def variant(text: str, name: str, version: str) -> str:
    if not isinstance(name, str) or not _VARIANT.fullmatch(name):
        raise ValueError(f"variant name {name!r} must be kebab-case, like pr-16961")
    if not isinstance(version, str) or not _VERSION.fullmatch(version):
        raise ValueError(f"version {version!r} must look like 2.22.0")
    data = _load(text)
    target = data.get("target")
    if not isinstance(target, dict) or "version" not in target:
        raise ValueError("scenario must have target.version")
    if "variant" in target:
        raise ValueError("scenario already has target.variant, it has no variant control")
    _rename(data, f"{name}-control", "Variant", f" on Medusa {version} with {name}")
    rewritten = {}
    for key, value in target.items():
        rewritten[key] = version if key == "version" else value
        if key == "servers":
            rewritten["variant"] = name
    rewritten.setdefault("variant", name)
    data["target"] = rewritten
    return _dump(data)


def main(argv: list[str]) -> int:
    build = one_server
    if argv[:1] == ["--redis-locking"]:
        build = redis_locking
        argv = argv[1:]
    elif argv[:1] == ["--variant"] and len(argv) >= 3:
        name, version = argv[1], argv[2]

        def build(text: str) -> str:
            return variant(text, name, version)

        argv = argv[3:]
    if len(argv) != 1 or argv[0].startswith("-"):
        print(USAGE, file=sys.stderr)
        return 2
    try:
        with open(argv[0], encoding="utf-8") as f:
            text = f.read()
        sys.stdout.write(build(text))
    except (OSError, ValueError, yaml.YAMLError) as err:
        print(f"shortfall.control: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
