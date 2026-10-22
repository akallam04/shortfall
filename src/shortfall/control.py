import sys

import yaml

MAX_NAME = 64


def one_server(text: str) -> str:
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError("scenario must be a mapping")
    target = data.get("target")
    if (
        not isinstance(target, dict)
        or target.get("servers") != 2
        or type(target["servers"]) is not int
    ):
        raise ValueError(
            "scenario must have target.servers 2, a one-server scenario has no one-server control"
        )
    name = data.get("name")
    if not isinstance(name, str) or not name:
        raise ValueError("scenario must have a name")
    control_name = f"{name}-control"
    if len(control_name) > MAX_NAME:
        raise ValueError(f"control name {control_name!r} is over {MAX_NAME} characters")

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

    data["name"] = control_name
    description = data.get("description")
    prefix = f"One-server control of {name}. "
    data["description"] = prefix + description if isinstance(description, str) else prefix.strip()

    return yaml.safe_dump(
        data, sort_keys=False, default_flow_style=False, allow_unicode=True, width=80
    )


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: python -m shortfall.control <scenario.yaml>", file=sys.stderr)
        return 2
    try:
        with open(argv[0], encoding="utf-8") as f:
            text = f.read()
        sys.stdout.write(one_server(text))
    except (OSError, ValueError, yaml.YAMLError) as err:
        print(f"shortfall.control: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
