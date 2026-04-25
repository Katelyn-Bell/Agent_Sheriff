from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from agentsheriff.models.dto import SkillCommandDTO, SkillDTO
from agentsheriff.skills.parser import ParsedSkill, parse_skill_md


_DEFAULT_FIXTURES = Path(__file__).parent / "fixtures"


def skills_directory() -> Path:
    """Resolve the directory containing installed skill packages."""

    override = os.environ.get("AGENTSHERIFF_SKILLS_DIR")
    if override:
        return Path(override).expanduser().resolve()
    return _DEFAULT_FIXTURES


def installed_skills() -> list[SkillDTO]:
    """Return every SKILL.md found under the configured skills directory."""

    return [_to_dto(parsed) for parsed in _discover()]


def get_skill(skill_id: str) -> SkillDTO | None:
    for parsed in _discover():
        if parsed.id == skill_id:
            return _to_dto(parsed)
    return None


def get_parsed_skill(skill_id: str) -> ParsedSkill | None:
    for parsed in _discover():
        if parsed.id == skill_id:
            return parsed
    return None


def _discover() -> list[ParsedSkill]:
    directory = skills_directory()
    if not directory.exists():
        return []
    parsed: list[ParsedSkill] = []
    for skill_md in sorted(directory.rglob("SKILL.md")):
        try:
            text = skill_md.read_text(encoding="utf-8")
        except OSError:
            continue
        try:
            parsed.append(
                parse_skill_md(
                    text,
                    default_id=skill_md.parent.name,
                    default_name=skill_md.parent.name.replace("-", " ").title(),
                )
            )
        except ValueError:
            continue
    return parsed


def _to_dto(parsed: ParsedSkill) -> SkillDTO:
    commands = [
        SkillCommandDTO(
            name=command.name,
            flags=list(command.flags),
            risky_flags=list(command.risky_flags),
            description=command.description,
            example=command.example,
        )
        for command in parsed.commands
    ]
    return SkillDTO(
        id=parsed.id,
        name=parsed.name,
        description=parsed.description,
        base_command=parsed.base_command,
        commands=commands,
        risky_flags=list(parsed.risky_flags),
    )


@lru_cache(maxsize=1)
def _cached_skills() -> tuple[ParsedSkill, ...]:  # pragma: no cover - reserved for future caching
    return tuple(_discover())
