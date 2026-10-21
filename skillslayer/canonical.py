"""The canonical model every source is translated into.

Each connector speaks its system's language (Workday worker, SuccessFactors User
plus EmpJob, Jira account, LMS row) and hands back these shapes. Everything
downstream (identity, readiness, inference, write-back) only knows these.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class SourcePerson:
    source: str                  # workday | successfactors | jira | lms
    source_id: str
    display: str
    first: str | None = None
    last: str | None = None
    email: str | None = None
    hire_date: date | None = None
    job_id: str | None = None
    manager_id: str | None = None
    country: str | None = None
    active: bool = True
    legacy_ids: dict[str, str] = field(default_factory=dict)
    updated: date | None = None

    @property
    def key(self) -> str:
        return f"{self.source}:{self.source_id}"


@dataclass
class Job:
    source: str
    job_id: str
    title: str
    description: str
    language: str | None
    updated: date | None
    active: bool = True

    @property
    def key(self) -> str:
        return f"{self.source}:{self.job_id}"


@dataclass
class Activity:
    """A piece of work or learning that can carry skill evidence."""
    source: str
    kind: str                    # ticket | course | about
    ref: str                     # text id: issue key, course:<id>, about:<userId>
    person_key: str              # SourcePerson.key of whoever did it
    text: str
    on: date | None


@dataclass
class LibrarySkill:
    """An entry in the customer's own skills or competency library."""
    source: str
    skill_id: str
    names: list[str]


@dataclass
class ProfileSkill:
    """A skill currently on a worker's profile in the HCM, and who put it there."""
    worker_id: str
    name: str
    skill_id: str | None
    source: str                  # employee | skills-layer
