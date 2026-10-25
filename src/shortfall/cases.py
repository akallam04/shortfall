import datetime
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

SCHEMA = "shortfall.case/v1"
ENGINES = ("medusa",)
RULES = (
    "no_oversell",
    "reserved_matches_reservations",
    "one_order_per_cart",
    "no_orphaned_orders",
)
CONTROL_KINDS = ("one-server", "fixed-version", "none")

_ID = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
_VERSION = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")
_ISSUE_URL = re.compile(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/issues/[1-9][0-9]*")
_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")

_TOP = (
    "schema",
    "id",
    "title",
    "engine",
    "versions",
    "issue",
    "rule",
    "control",
    "reference",
    "agent_sees",
    "notes",
)
_ISSUE = ("url", "opened", "state")
_CONTROL = ("kind", "version", "reason")
_REFERENCE = ("file", "source")
_AGENT_SEES = ("guided", "unguided")


@dataclass(frozen=True)
class Issue:
    url: str
    opened: datetime.date
    state: str


@dataclass(frozen=True)
class Control:
    kind: str
    version: str | None
    reason: str | None


@dataclass(frozen=True)
class Reference:
    file: str
    source: str


@dataclass(frozen=True)
class AgentSees:
    guided: tuple[str, ...]
    unguided: tuple[str, ...]


@dataclass(frozen=True)
class Case:
    folder: Path
    id: str
    title: str
    engine: str
    versions: tuple[str, ...]
    issue: Issue
    rule: str
    control: Control
    reference: Reference
    agent_sees: AgentSees
    notes: str | None


class _StrictLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader, node, deep=False):
    keys = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in keys:
            raise yaml.constructor.ConstructorError(
                None, None, f"duplicate key {key!r}", key_node.start_mark
            )
        keys.add(key)
    return loader.construct_mapping(node, deep=deep)


_StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


def strict_load(text: str):
    return yaml.load(text, Loader=_StrictLoader)


def _is_text(value) -> bool:
    return isinstance(value, str) and value.strip() != ""


def _mapping(data, where, allowed, problems) -> dict:
    if not isinstance(data, dict):
        problems.append(f"{where} must be a mapping")
        return {}
    for key in data:
        if key not in allowed:
            name = f"{where}.{key}" if where != "case" else str(key)
            problems.append(f"unknown field {name}")
    return data


def _text(data, key, where, problems) -> str | None:
    if key not in data:
        problems.append(f"{where} is required")
        return None
    value = data[key]
    if not _is_text(value):
        problems.append(f"{where} must be plain text, not empty")
        return None
    return value


def _text_list(data, key, where, problems) -> tuple[str, ...]:
    if key not in data:
        problems.append(f"{where} is required")
        return ()
    value = data[key]
    if not isinstance(value, list) or not value:
        problems.append(f"{where} must be a list of one or more items")
        return ()
    for i, item in enumerate(value):
        if not _is_text(item):
            problems.append(f"{where}[{i}] must be plain text, not empty")
    return tuple(value)


def _date(value) -> datetime.date | None:
    if isinstance(value, datetime.datetime):
        return None
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, str) and _DATE.fullmatch(value):
        try:
            return datetime.date.fromisoformat(value)
        except ValueError:
            return None
    return None


def load_case(folder: str | Path) -> Case:
    folder = Path(folder)
    path = folder / "case.yaml"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as err:
        raise ValueError(f"{path}: cannot read: {err}") from err
    try:
        data = strict_load(text)
    except yaml.YAMLError as err:
        raise ValueError(f"{path}: invalid YAML: {err}") from err

    problems: list[str] = []
    top = _mapping(data, "case", _TOP, problems)

    if "schema" not in top:
        problems.append("schema is required")
    elif top["schema"] != SCHEMA:
        problems.append(f"schema must be {SCHEMA}")

    case_id = None
    if "id" not in top:
        problems.append("id is required")
    elif not isinstance(top["id"], str) or not _ID.fullmatch(top["id"]):
        problems.append("id must be kebab-case")
    elif top["id"] != folder.name:
        problems.append(f"id must equal the folder name {folder.name!r}")
    else:
        case_id = top["id"]

    title = _text(top, "title", "title", problems)

    engine = None
    if "engine" not in top:
        problems.append("engine is required")
    elif top["engine"] not in ENGINES:
        problems.append(f"engine must be one of {', '.join(ENGINES)}")
    else:
        engine = top["engine"]

    versions: tuple[str, ...] = ()
    if "versions" not in top:
        problems.append("versions is required")
    elif not isinstance(top["versions"], list) or not top["versions"]:
        problems.append("versions must be a list of one or more versions")
    else:
        for i, v in enumerate(top["versions"]):
            if not isinstance(v, str) or not _VERSION.fullmatch(v):
                problems.append(f"versions[{i}] must be a version like 2.21.2")
        if len(set(map(str, top["versions"]))) != len(top["versions"]):
            problems.append("versions must not repeat")
        versions = tuple(top["versions"])

    issue = None
    if "issue" not in top:
        problems.append("issue is required")
    else:
        raw = _mapping(top["issue"], "issue", _ISSUE, problems)
        url = None
        if "url" not in raw:
            problems.append("issue.url is required")
        elif not isinstance(raw["url"], str) or not _ISSUE_URL.fullmatch(raw["url"]):
            problems.append("issue.url must be https://github.com/<owner>/<repo>/issues/<number>")
        else:
            url = raw["url"]
        opened = None
        if "opened" not in raw:
            problems.append("issue.opened is required")
        else:
            opened = _date(raw["opened"])
            if opened is None:
                problems.append("issue.opened must be a date, YYYY-MM-DD")
        state = _text(raw, "state", "issue.state", problems)
        if url and opened and state:
            issue = Issue(url=url, opened=opened, state=state)

    rule = None
    if "rule" not in top:
        problems.append("rule is required")
    elif top["rule"] not in RULES:
        problems.append(f"rule must be one of {', '.join(RULES)}")
    else:
        rule = top["rule"]

    control = None
    if "control" not in top:
        problems.append("control is required")
    else:
        raw = _mapping(top["control"], "control", _CONTROL, problems)
        kind = raw.get("kind")
        if "kind" not in raw:
            problems.append("control.kind is required")
        elif kind not in CONTROL_KINDS:
            problems.append(f"control.kind must be one of {', '.join(CONTROL_KINDS)}")
            kind = None
        version = None
        if kind == "fixed-version":
            if "version" not in raw:
                problems.append("control.version is required with fixed-version")
            elif not isinstance(raw["version"], str) or not _VERSION.fullmatch(raw["version"]):
                problems.append("control.version must be a version like 2.21.2")
            else:
                version = raw["version"]
        elif "version" in raw:
            problems.append("control.version is only allowed with fixed-version")
        reason = None
        if kind == "none":
            reason = _text(raw, "reason", "control.reason", problems)
        elif "reason" in raw:
            problems.append("control.reason is only allowed with none")
        if kind:
            control = Control(kind=kind, version=version, reason=reason)

    reference = None
    if "reference" not in top:
        problems.append("reference is required")
    else:
        raw = _mapping(top["reference"], "reference", _REFERENCE, problems)
        ref_file = None
        if "file" not in raw:
            problems.append("reference.file is required")
        else:
            name = raw["file"]
            if (
                not isinstance(name, str)
                or not name
                or name != Path(name).name
                or name in (".", "..")
                or not (folder / name).is_file()
            ):
                problems.append("reference.file must name a file in the case folder")
            else:
                ref_file = name
        source = _text(raw, "source", "reference.source", problems)
        if ref_file and source:
            reference = Reference(file=ref_file, source=source)

    agent_sees = None
    if "agent_sees" not in top:
        problems.append("agent_sees is required")
    else:
        raw = _mapping(top["agent_sees"], "agent_sees", _AGENT_SEES, problems)
        guided = _text_list(raw, "guided", "agent_sees.guided", problems)
        unguided = _text_list(raw, "unguided", "agent_sees.unguided", problems)
        agent_sees = AgentSees(guided=guided, unguided=unguided)

    notes = None
    if "notes" in top:
        notes = _text(top, "notes", "notes", problems)

    if problems:
        raise ValueError(f"{path}: " + "; ".join(problems))
    return Case(
        folder=folder,
        id=case_id,
        title=title,
        engine=engine,
        versions=versions,
        issue=issue,
        rule=rule,
        control=control,
        reference=reference,
        agent_sees=agent_sees,
        notes=notes,
    )
