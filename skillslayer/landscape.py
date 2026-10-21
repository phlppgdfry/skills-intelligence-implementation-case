"""Pull the whole customer landscape through the connectors into one in-memory snapshot."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from .canonical import Activity, Job, LibrarySkill, ProfileSkill, SourcePerson
from .config import AS_OF, SOURCES
from .sources import connectors as c
from .sources.http import Client

TENANT = "norvane_impl"   # the implementation tenant; production is configured per environment, never in code


@dataclass
class Landscape:
    workday: list[SourcePerson]
    sf: list[SourcePerson]
    jira: list[SourcePerson]
    jobs: list[Job]
    activities: list[Activity]
    profile_skills: list[ProfileSkill]
    libraries: list[LibrarySkill]
    optouts: dict
    stats: list[c.FetchStats] = field(default_factory=list)
    retries: int = 0
    as_of: date = AS_OF

    @property
    def lms_emails(self) -> list[str]:
        return sorted({a.person_key.split(":", 1)[1] for a in self.activities if a.source == "lms"})


def fetch(base_url: str, token: str, time_scale: float = 0.01, updated_from: date | None = None) -> Landscape:
    wd = Client(base_url, token, time_scale=time_scale)
    workers, wd_stats = c.workday_workers(wd, TENANT, updated_from=updated_from)
    jobs = c.workday_jobs(c.workday_report(wd, TENANT, "Job_Profiles_for_Skills_Layer"))
    library = c.workday_report(wd, TENANT, "Skills_Library")

    sf = Client(base_url, token, time_scale=time_scale)
    users, s1 = c.sf_entity(sf, "User")
    empjob, s2 = c.sf_entity(sf, "EmpJob")
    jobcodes, s3 = c.sf_entity(sf, "FOJobCode")
    about, s4 = c.sf_entity(sf, "cust_AboutMe")
    sf_people = c.sf_people(users, c.sf_current_jobs(empjob, AS_OF))
    jobs += c.sf_jobs(jobcodes)

    jr = Client(base_url, token, time_scale=time_scale)
    issues, j_stats = c.jira_issues(jr, 'project = ELEC AND statusCategory = Done AND status = "Done"')
    jira_people = c.jira_users(jr)

    acts = c.jira_activities(issues) + c.sf_about(about) + c.lms_completions(SOURCES / "lms" / "completions.csv")
    return Landscape(
        workday=workers, sf=sf_people, jira=jira_people, jobs=jobs, activities=acts,
        profile_skills=c.workday_profile_skills(SOURCES / "workday" / "worker_skills.json"),
        libraries=c.libraries(library, SOURCES / "successfactors" / "competency_library.json"),
        optouts=c.optouts(SOURCES / "consent" / "optouts.json"),
        stats=[wd_stats, s1, s2, s3, s4, j_stats],
        retries=wd.retries + sf.retries + jr.retries,
    )
