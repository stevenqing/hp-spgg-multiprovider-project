"""Utilities for reconstructing SOTOPIA-Hard cases from public episode logs."""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sotopia.database.persistent_profile import AgentProfile, EnvironmentProfile, RelationshipType


@dataclass(frozen=True)
class HardCase:
    combo_pk: str
    env_id: str
    agent_ids: tuple[str, str]
    codename: str
    scenario: str
    agent_names: tuple[str, str]
    agent_backgrounds: tuple[str, str]
    agent_goals: tuple[str, str]


def load_hard_cases(
    benchmark_agents_path: Path,
    episodes_jsonl_path: Path,
    cache_path: Path | None = None,
    rebuild_cache: bool = False,
) -> list[HardCase]:
    if cache_path is not None and cache_path.exists() and not rebuild_cache:
        return [_case_from_dict(item) for item in json.loads(cache_path.read_text(encoding="utf-8"))]

    combos = json.loads(benchmark_agents_path.read_text(encoding="utf-8"))
    wanted = {(item["env_id"], tuple(item["agent_ids"])): item for item in combos}
    found: dict[tuple[str, tuple[str, ...]], dict[str, Any]] = {}

    with episodes_jsonl_path.open(encoding="utf-8") as handle:
        for line in handle:
            episode = json.loads(line)
            key = (episode.get("environment_id"), tuple(episode.get("agent_ids", [])))
            if key in wanted and key not in found:
                found[key] = episode
                if len(found) == len(wanted):
                    break

    missing = [key for key in wanted if key not in found]
    if missing:
        raise RuntimeError(f"Missing {len(missing)} SOTOPIA-Hard combos in episode JSONL: {missing[:3]}")

    cases: list[HardCase] = []
    for key, combo in wanted.items():
        episode = found[key]
        backgrounds = _literal_dict(episode["agents_background"])
        goals = _literal_dict(episode["social_goals"])
        names = list(backgrounds.keys())
        if len(names) != 2:
            raise RuntimeError(f"Expected two agents for combo {combo.get('pk')}, got {names}")
        cases.append(
            HardCase(
                combo_pk=combo.get("pk", ""),
                env_id=episode["environment_id"],
                agent_ids=tuple(episode["agent_ids"]),
                codename=episode.get("codename", ""),
                scenario=episode.get("scenario", ""),
                agent_names=(names[0], names[1]),
                agent_backgrounds=(str(backgrounds[names[0]]), str(backgrounds[names[1]])),
                agent_goals=(str(goals[names[0]]), str(goals[names[1]])),
            )
        )

    if cache_path is not None:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps([_case_to_dict(case) for case in cases], indent=2), encoding="utf-8")
    return cases


def make_environment_profile(case: HardCase) -> EnvironmentProfile:
    return EnvironmentProfile(
        pk=case.env_id,
        codename=case.codename,
        scenario=case.scenario,
        agent_goals=list(case.agent_goals),
        relationship=RelationshipType.stranger,
        source="cmu-lti/sotopia public episode log reconstruction",
        tag="sotopia_hard_reconstructed",
    )


def make_agent_profiles(case: HardCase) -> list[AgentProfile]:
    return [
        _profile_from_background(agent_id, name, background)
        for agent_id, name, background in zip(case.agent_ids, case.agent_names, case.agent_backgrounds)
    ]


def _literal_dict(raw: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    parsed = ast.literal_eval(raw)
    if not isinstance(parsed, dict):
        raise ValueError(f"Expected dict-like field, got {type(parsed)}")
    return parsed


def _profile_from_background(agent_id: str, full_name: str, background: str) -> AgentProfile:
    first_name, last_name = _split_name(full_name)
    age = 0
    gender = ""
    occupation = ""
    pronouns = ""
    match = re.search(r"is a (\d+)-year-old ([^.]*)\. ([^.]* pronouns)\.", background)
    if match:
        age = int(match.group(1))
        demographic = match.group(2).strip()
        pronouns = match.group(3).strip()
        parts = demographic.split()
        if parts:
            gender = {"male": "Man", "female": "Woman", "nonbinary": "Nonbinary"}.get(parts[0].lower(), "")
            occupation = " ".join(parts[1:]) if gender else demographic

    personality = ""
    public_info = background
    secret = ""
    personality_marker = "Personality and values description:"
    if personality_marker in background:
        public_info, personality_tail = background.split(personality_marker, 1)
        personality = personality_tail.strip()
    secret_match = re.search(r"secrets?:\s*(.*)$", background)
    if secret_match:
        secret = secret_match.group(1).strip()
        personality = re.sub(r"\s*\w+'s secrets?:\s*.*$", "", personality).strip()

    return AgentProfile(
        pk=agent_id,
        first_name=first_name,
        last_name=last_name,
        age=age,
        occupation=occupation or "participant",
        gender=gender,
        gender_pronoun=pronouns,
        public_info=public_info.strip(),
        personality_and_values=personality,
        secret=secret,
        tag="sotopia_hard_reconstructed",
    )


def _split_name(full_name: str) -> tuple[str, str]:
    parts = full_name.strip().split()
    if not parts:
        return "Agent", "Unknown"
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def _case_to_dict(case: HardCase) -> dict[str, Any]:
    return {
        "combo_pk": case.combo_pk,
        "env_id": case.env_id,
        "agent_ids": list(case.agent_ids),
        "codename": case.codename,
        "scenario": case.scenario,
        "agent_names": list(case.agent_names),
        "agent_backgrounds": list(case.agent_backgrounds),
        "agent_goals": list(case.agent_goals),
    }


def _case_from_dict(item: dict[str, Any]) -> HardCase:
    return HardCase(
        combo_pk=item["combo_pk"],
        env_id=item["env_id"],
        agent_ids=tuple(item["agent_ids"]),
        codename=item["codename"],
        scenario=item["scenario"],
        agent_names=tuple(item["agent_names"]),
        agent_backgrounds=tuple(item["agent_backgrounds"]),
        agent_goals=tuple(item["agent_goals"]),
    )