"""A transparent stand-in for a skills inference engine.

This is NOT a vendor's model. It exists so the implementation around it (sources,
identity, governance, validation, write-back, evals) can be built and measured
end to end. It does two things:

1. extract(): find skill mentions in a text, with evidence (form, sentence, status)
2. profile(): fuse evidence from several sources into a per-person skill profile

Three extraction configurations are compared in the evals:

    A  canonical skill names only            (what a quick keyword search does)
    B  A + aliases in EN, NL, DE and FR       (the multilingual taxonomy)
    C  B + guards: negation, aspiration and ambiguous words need context

Everything is deterministic and explainable: each suggestion carries the
sentences it came from, so an employee or an HR business partner can see why.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from datetime import date
from functools import cache

from .config import AS_OF
from .taxonomy import Taxonomy, load

CONFIGS = ("A", "B", "C")

# Cues that, before a mention in the same sentence, mean "this is not a skill (yet)".
NEGATION = ("no experience with", "no experience in", "without", "not required", "geen ervaring met", "geen kennis van",
            "zonder", "keine erfahrung mit", "keine kenntnisse in", "ohne", "pas d'expérience en", "pas d'expérience avec", "sans")
ASPIRATION = ("would like to learn", "want to learn", "keen to learn", "wil graag", "wil ik leren", "möchte", "würde gerne",
              "aimerais apprendre", "souhaite apprendre")
CUE_WINDOW = 45       # characters before the mention that are searched for a cue
CONTEXT_WINDOW = 80   # characters around an ambiguous mention that are searched for a context word

SENTENCE = re.compile(r"[^.!?;]+[.!?;]?")


@dataclass(frozen=True)
class Mention:
    skill_id: str
    form: str
    start: int
    end: int
    sentence: str
    status: str  # accepted | negated | aspiration | ambiguous


@dataclass
class Evidence:
    skill_id: str
    kind: str        # job | ticket | course | about
    ref: str         # where it came from (job id, issue key, course id, profile field)
    sentence: str
    on: date | None  # when the evidence happened, if known
    weight: float = 0.0


@dataclass
class SkillScore:
    skill_id: str
    score: float
    evidence: list[Evidence] = field(default_factory=list)


@cache
def _patterns(config: str, version: str) -> list[tuple[re.Pattern, str, str, bool]]:
    tax = load()
    forms: list[tuple[str, str, bool]] = []
    for s in tax.skills:
        forms.append((s.name, s.id, False))
        if config in ("B", "C"):
            for a in s.all_aliases():
                forms.append((a, s.id, bool(s.context) and a.casefold() != s.name.casefold()))
    seen: set[tuple[str, str]] = set()
    out = []
    for form, sid, ambiguous in sorted(forms, key=lambda f: -len(f[0])):
        key = (form.casefold(), sid)
        if key in seen:
            continue
        seen.add(key)
        out.append((re.compile(r"(?<!\w)" + re.escape(form.casefold()) + r"(?!\w)"), sid, form, ambiguous))
    return out


def _sentence_at(text: str, pos: int) -> tuple[int, str]:
    for m in SENTENCE.finditer(text):
        if m.start() <= pos < m.end():
            return m.start(), m.group().strip()
    return 0, text


def extract(text: str, config: str = "C", taxonomy: Taxonomy | None = None) -> list[Mention]:
    """All mentions found in `text`, longest form first, without overlaps."""
    if config not in CONFIGS:
        raise ValueError(f"unknown config {config!r}")
    tax = taxonomy or load()
    folded = text.casefold()
    taken: list[tuple[int, int]] = []
    found: list[Mention] = []
    for pat, sid, form, ambiguous in _patterns(config, tax.version):
        for m in pat.finditer(folded):
            if any(m.start() < e and s < m.end() for s, e in taken):
                continue
            taken.append((m.start(), m.end()))
            s_start, sentence = _sentence_at(text, m.start())
            status = "accepted"
            if config == "C":
                before = folded[max(s_start, m.start() - CUE_WINDOW):m.start()]
                if any(c in before for c in NEGATION):
                    status = "negated"
                elif any(c in before for c in ASPIRATION):
                    status = "aspiration"
                elif ambiguous:
                    around = folded[max(0, m.start() - CONTEXT_WINDOW):m.end() + CONTEXT_WINDOW]
                    words = tax.by_id[sid].context
                    if not any(re.search(r"(?<!\w)" + re.escape(w) + r"(?!\w)", around) for w in words):
                        status = "ambiguous"
            found.append(Mention(sid, text[m.start():m.end()], m.start(), m.end(), sentence, status))
    return sorted(found, key=lambda x: x.start)


def skills_in(text: str, config: str = "C") -> set[str]:
    return {m.skill_id for m in extract(text, config) if m.status == "accepted"}


# ------------------------------------------------------------------------ profiles
# How much one piece of evidence says about a person, before recency decay.
# A job profile says what the role needs, not what this person can do; a resolved
# ticket is direct evidence of work; a course says someone learned about it.
WEIGHTS = {"job": 0.35, "ticket": 0.60, "course": 0.30, "about": 0.60}
# "Broad" lets a job profile alone produce a suggestion; the default needs corroboration
# from work or learning. The evals compare both (ADR-0009).
BROAD_WEIGHTS = {**WEIGHTS, "job": 0.45}
HALF_LIFE_DAYS = 548      # evidence loses half its weight in 18 months
MAX_AGE_DAYS = 3 * 365    # older evidence is ignored
SUGGEST_AT = 0.4          # score from which a skill is suggested to the employee


def weight(ev: Evidence, as_of: date = AS_OF, weights: dict[str, float] | None = None) -> float:
    w = (weights or WEIGHTS)[ev.kind]
    if ev.on is None or ev.kind in ("job", "about"):
        return w
    age = (as_of - ev.on).days
    if age > MAX_AGE_DAYS:
        return 0.0
    return w * math.pow(0.5, max(age, 0) / HALF_LIFE_DAYS)


def profile(evidence: list[Evidence], as_of: date = AS_OF, weights: dict[str, float] | None = None) -> dict[str, SkillScore]:
    """Noisy-OR fusion: independent pieces of evidence each close part of the gap to 1."""
    out: dict[str, SkillScore] = {}
    for ev in evidence:
        ev.weight = round(weight(ev, as_of, weights), 4)
        if ev.weight == 0:
            continue
        s = out.setdefault(ev.skill_id, SkillScore(ev.skill_id, 0.0))
        s.evidence.append(ev)
    for s in out.values():
        miss = 1.0
        for ev in s.evidence:
            miss *= 1 - ev.weight
        s.score = round(1 - miss, 4)
        s.evidence.sort(key=lambda e: -e.weight)
    return out


def suggestions(scores: dict[str, SkillScore], threshold: float = SUGGEST_AT) -> list[SkillScore]:
    return sorted((s for s in scores.values() if s.score >= threshold), key=lambda s: (-s.score, s.skill_id))
