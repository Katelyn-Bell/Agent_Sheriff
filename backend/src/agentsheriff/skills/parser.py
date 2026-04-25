from __future__ import annotations

import re
import shlex
from dataclasses import dataclass, field
from typing import Iterable

import yaml


RISKY_FLAGS: frozenset[str] = frozenset(
    {
        "--prod",
        "--production",
        "--force",
        "-f",
        "--yes",
        "-y",
        "--all",
        "--no-confirm",
        "--no-dry-run",
    }
)

RISKY_SUBCOMMAND_TOKENS: frozenset[str] = frozenset(
    {"cancel-all", "transfer", "withdraw", "delete", "drop", "wipe", "purge"}
)

BOOLEAN_FLAGS: frozenset[str] = frozenset(
    {
        "--prod",
        "--production",
        "--yes",
        "-y",
        "--force",
        "-f",
        "--all",
        "--no-color",
        "--no-confirm",
        "--no-dry-run",
        "--dry-run",
        "--verbose",
        "-v",
        "--quiet",
        "-q",
        "--help",
        "-h",
    }
)


@dataclass(frozen=True)
class ParsedSkillCommand:
    name: str
    flags: tuple[str, ...]
    risky_flags: tuple[str, ...]
    example: str | None = None
    description: str | None = None


@dataclass(frozen=True)
class ParsedSkill:
    id: str
    name: str
    description: str | None
    base_command: str
    commands: tuple[ParsedSkillCommand, ...] = field(default_factory=tuple)

    @property
    def risky_flags(self) -> tuple[str, ...]:
        seen: list[str] = []
        for command in self.commands:
            for flag in command.risky_flags:
                if flag not in seen:
                    seen.append(flag)
        return tuple(seen)


_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_FENCED_BLOCK_RE = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
_COMMAND_REFERENCE_RE = re.compile(
    r"^##\s+command\s+reference\s*$(.*?)(?=^##\s|\Z)",
    re.IGNORECASE | re.MULTILINE | re.DOTALL,
)


def parse_skill_md(
    text: str,
    *,
    default_id: str | None = None,
    default_name: str | None = None,
) -> ParsedSkill:
    """Parse a SKILL.md document and return its structured command vocabulary.

    Precedence for command extraction:
    1. If the body contains a ``## Command Reference`` section (case-insensitive
       H2), parse the markdown table that follows. Each row's first cell is
       treated as the subcommand (or full invocation suffix if it contains
       flags/args). Surrounding backticks are stripped.
    2. Otherwise, fall back to scanning every fenced code block / inline code
       span for lines that begin with ``base_command``.

    The fallback is also used when the ``## Command Reference`` section yields
    zero commands (e.g. malformed table).
    """

    metadata, body = _split_frontmatter(text)
    base_command = _coerce_str(metadata.get("base_command")) or _infer_base_command(body)
    if not base_command:
        raise ValueError("Could not determine base_command from SKILL.md frontmatter or body.")

    skill_id = _coerce_str(metadata.get("id")) or default_id or _slugify(base_command)
    skill_name = _coerce_str(metadata.get("name")) or default_name or skill_id.replace("-", " ").title()
    description = _coerce_str(metadata.get("description"))

    invocations = list(_iter_command_reference_invocations(body, base_command))
    if not invocations:
        invocations = list(_iter_invocations(body, base_command))
    commands = _group_commands(invocations)

    return ParsedSkill(
        id=skill_id,
        name=skill_name,
        description=description,
        base_command=base_command,
        commands=tuple(commands),
    )


def _split_frontmatter(text: str) -> tuple[dict[str, object], str]:
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    try:
        metadata = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        metadata = {}
    if not isinstance(metadata, dict):
        metadata = {}
    return metadata, text[match.end():]


def _infer_base_command(body: str) -> str | None:
    counts: dict[str, int] = {}
    for block in _FENCED_BLOCK_RE.finditer(body):
        for line in block.group(1).splitlines():
            token = _first_token(line)
            if token:
                counts[token] = counts.get(token, 0) + 1
    if not counts:
        return None
    return max(counts.items(), key=lambda kv: kv[1])[0]


def _iter_command_reference_invocations(body: str, base_command: str) -> Iterable[str]:
    r"""Yield invocations from the ``## Command Reference`` table.

    Scans every cell of every data row and picks the cell that contains a
    backticked invocation starting with ``base_command``. If no cell does, falls
    back to the first non-empty cell with surrounding backticks stripped — that
    handles the legacy table format where the subcommand sat naked in column 1.
    Section-header rows (single cell with no command) and the markdown header
    row are skipped naturally.
    """

    match = _COMMAND_REFERENCE_RE.search(body)
    if not match:
        return
    section = match.group(1)

    seen: set[str] = set()
    past_separator = False
    for raw_line in section.splitlines():
        line = raw_line.strip()
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if not cells:
            continue
        # The markdown table separator (e.g. "| --- | --- |") marks the end of
        # the header row; rows above it are column labels we should skip.
        if cells[0] and set(cells[0]) <= {"-", ":", " "}:
            past_separator = True
            continue
        if not past_separator:
            continue

        invocation: str | None = None
        for cell in cells:
            for token in _INLINE_CODE_RE.findall(cell):
                stripped = token.strip()
                if stripped.startswith(f"{base_command} ") or stripped == base_command:
                    invocation = stripped
                    break
            if invocation:
                break

        if invocation is None:
            # Legacy layout: no backticked invocation, but column 1 holds the
            # bare subcommand (e.g. ``auth login``). Synthesize an invocation.
            first = cells[0].strip("`").strip()
            if not first:
                continue
            # Skip section-header rows like ``| **Auth** |`` — they hold
            # category labels, not commands.
            if first.startswith("**") and first.endswith("**"):
                continue
            invocation = f"{base_command} {first}"

        if invocation in seen:
            continue
        seen.add(invocation)
        yield invocation


def _iter_invocations(body: str, base_command: str) -> Iterable[str]:
    seen: set[str] = set()
    sources: list[str] = []
    for block in _FENCED_BLOCK_RE.finditer(body):
        sources.extend(block.group(1).splitlines())
    sources.extend(match.group(1) for match in _INLINE_CODE_RE.finditer(body))

    for raw in sources:
        line = raw.strip()
        if not line:
            continue
        line = line.lstrip("$> ").strip()
        if not line.startswith(base_command):
            continue
        if line in seen:
            continue
        seen.add(line)
        yield line


def _group_commands(invocations: Iterable[str]) -> list[ParsedSkillCommand]:
    grouped: dict[str, dict[str, object]] = {}

    for invocation in invocations:
        try:
            tokens = shlex.split(invocation, posix=True)
        except ValueError:
            tokens = invocation.split()
        if not tokens:
            continue
        # Drop the base command token (and any path prefix like ./kalshi-cli).
        tokens = tokens[1:]
        if not tokens:
            continue
        positionals, flags = _split_positionals_and_flags(tokens)
        if not positionals:
            continue
        name = " ".join(positionals)

        bucket = grouped.setdefault(
            name,
            {"flags": [], "example": invocation, "positionals": list(positionals)},
        )
        bucket_flags: list[str] = bucket["flags"]  # type: ignore[assignment]
        for flag in flags:
            if flag not in bucket_flags:
                bucket_flags.append(flag)

    commands: list[ParsedSkillCommand] = []
    for name, payload in grouped.items():
        flag_list: list[str] = payload["flags"]  # type: ignore[assignment]
        positionals: list[str] = payload["positionals"]  # type: ignore[assignment]
        risky = _risky_flags_for(flag_list, positionals)
        commands.append(
            ParsedSkillCommand(
                name=name,
                flags=tuple(flag_list),
                risky_flags=tuple(risky),
                example=payload["example"],  # type: ignore[arg-type]
            )
        )
    commands.sort(key=lambda c: c.name)
    return commands


def _split_positionals_and_flags(tokens: list[str]) -> tuple[list[str], list[str]]:
    positionals: list[str] = []
    flags: list[str] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token.startswith("-"):
            flag, _, _inline_value = token.partition("=")
            flags.append(flag)
            if "=" in token or flag in BOOLEAN_FLAGS:
                index += 1
                continue
            # Consume the next token as this flag's value if it is not another flag.
            if index + 1 < len(tokens) and not tokens[index + 1].startswith("-"):
                index += 2
            else:
                index += 1
            continue
        # Drop CLI-doc placeholders (TICKER, ORDER_ID, EVENT_TICKER, GROUP_ID,
        # etc.) so the subcommand name stays stable across rows that vary only
        # by the example value passed in. We treat any token that's all-caps
        # plus underscores/digits as a placeholder.
        if _is_placeholder(token):
            index += 1
            continue
        positionals.append(token)
        index += 1
    return positionals, flags


def _is_placeholder(token: str) -> bool:
    if not token:
        return False
    if not any(ch.isalpha() for ch in token):
        return False
    return all(ch.isupper() or ch.isdigit() or ch == "_" for ch in token)


def _risky_flags_for(flags: list[str], positionals: list[str]) -> list[str]:
    risky = [flag for flag in flags if flag in RISKY_FLAGS]
    if any(token in RISKY_SUBCOMMAND_TOKENS for token in positionals):
        # Surface inherent subcommand risk as a synthetic marker so the
        # frontend can highlight the command even when no explicit flag is set.
        marker = "::risky-subcommand"
        if marker not in risky:
            risky.append(marker)
    return risky


def _first_token(line: str) -> str | None:
    cleaned = line.strip().lstrip("$> ").strip()
    if not cleaned:
        return None
    try:
        tokens = shlex.split(cleaned, posix=True)
    except ValueError:
        tokens = cleaned.split()
    return tokens[0] if tokens else None


def _coerce_str(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text or None
    return str(value).strip() or None


def _slugify(value: str) -> str:
    cleaned = "".join(char.lower() if char.isalnum() else "-" for char in value)
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-") or "skill"
