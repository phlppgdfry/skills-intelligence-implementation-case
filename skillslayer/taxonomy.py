"""The skills taxonomy: skills, clusters, domains and the surface forms that point to them."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

from .config import DATA


@dataclass(frozen=True)
class Skill:
    id: str
    name: str
    cluster: str
    domain: str
    aliases: dict[str, tuple[str, ...]] = field(default_factory=dict)
    context: tuple[str, ...] = ()

    def all_aliases(self) -> list[str]:
        return [a for forms in self.aliases.values() for a in forms]


@dataclass(frozen=True)
class Taxonomy:
    version: str
    skills: tuple[Skill, ...]

    @property
    def by_id(self) -> dict[str, Skill]:
        return {s.id: s for s in self.skills}

    def clusters(self) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        for s in self.skills:
            out.setdefault(s.cluster, []).append(s.id)
        return out


def load(path: Path | None = None) -> Taxonomy:
    return _load(str(path or DATA / "taxonomy.json"))


@cache
def _load(path: str) -> Taxonomy:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    skills = tuple(
        Skill(s["id"], s["name"], s["cluster"], s["domain"],
              {lang: tuple(forms) for lang, forms in s.get("aliases", {}).items()},
              tuple(s.get("context", ())))
        for s in raw["skills"]
    )
    return Taxonomy(raw["version"], skills)
