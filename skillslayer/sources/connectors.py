"""Connectors: read each system the way its API wants to be read, return canonical records.

Workday         REST (workers, offset/limit, delta on updatedFrom) + RaaS (custom reports)
SuccessFactors  OData v2 (server-side paging via __next, /Date(ms)/ literals, effective dating)
Jira Cloud      /rest/api/3/search/jql (nextPageToken), only the fields we need
LMS             CSV export over SFTP (here: a file)
Consent tool    JSON export of opt-outs
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path

from ..canonical import Activity, Job, LibrarySkill, ProfileSkill, SourcePerson
from .http import Client

ODATA_DATE = re.compile(r"/Date\((-?\d+)(?:[+-]\d{4})?\)/")
JIRA_FIELDS = ("summary", "assignee", "resolutiondate", "components")  # never description or comments: ADR-0002


@dataclass
class FetchStats:
    source: str
    records: int = 0
    pages: int = 0
    retries: int = 0
    notes: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------- helpers
def odata_date(value: str | None) -> date | None:
    """SuccessFactors OData v2 sends dates as /Date(1700000000000)/, in UTC milliseconds."""
    if not value:
        return None
    m = ODATA_DATE.fullmatch(value)
    if not m:
        raise ValueError(f"not an OData date: {value!r}")
    ms = int(m.group(1))
    if ms >= 253402214400000:  # 9999-12-31: SuccessFactors' "open end"
        return date.max
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).date()


def iso_date(value: str | None) -> date | None:
    return date.fromisoformat(value[:10]) if value else None


# ---------------------------------------------------------------------- Workday
def workday_workers(client: Client, tenant: str, updated_from: date | None = None, limit: int = 100) -> tuple[list[SourcePerson], FetchStats]:
    stats = FetchStats("workday")
    before = client.retries
    out: list[SourcePerson] = []
    offset, total = 0, None
    while total is None or offset < total:
        body = client.get_json(f"/workday/ccx/api/v1/{tenant}/workers",
                               {"offset": offset, "limit": limit, "updatedFrom": updated_from.isoformat() if updated_from else None})
        stats.pages += 1
        total = body["total"]
        for w in body["data"]:
            out.append(SourcePerson(
                "workday", w["id"], w["descriptor"], w["firstName"], w["lastName"], w.get("primaryWorkEmail"),
                iso_date(w.get("hireDate")), (w.get("jobProfile") or {}).get("id"), (w.get("manager") or {}).get("id"),
                w.get("location"), True,
                {"successfactors": w["legacySuccessFactorsId"]} if w.get("legacySuccessFactorsId") else {},
                iso_date(w.get("lastUpdated")),
            ))
        if not body["data"]:
            break
        offset += len(body["data"])
    stats.records, stats.retries = len(out), client.retries - before
    return out, stats


def workday_report(client: Client, tenant: str, report: str, owner: str = "ISU_SkillsLayer") -> list[dict]:
    """RaaS: a custom report exposed as a web service, owned by the integration system user."""
    return client.get_json(f"/workday/ccx/service/customreport2/{tenant}/{owner}/{report}", {"format": "json"})["Report_Entry"]


def workday_jobs(entries: list[dict]) -> list[Job]:
    return [Job("workday", e["Job_Profile_ID"], e["Job_Profile_Name"], e.get("Job_Description") or "", e.get("Language"),
                iso_date(e.get("Last_Updated")), e.get("Inactive") != "1") for e in entries]


def workday_profile_skills(path: Path) -> list[ProfileSkill]:
    return [ProfileSkill(r["worker"], r["skill"], r.get("skillId"), r["source"]) for r in json.loads(path.read_text(encoding="utf-8"))]


# ---------------------------------------------------------------------- SuccessFactors
def sf_entity(client: Client, entity: str) -> tuple[list[dict], FetchStats]:
    stats = FetchStats(f"successfactors:{entity}")
    before = client.retries
    rows: list[dict] = []
    url: str | None = f"/sf/odata/v2/{entity}?$format=json"
    while url:
        body = client.get_json(url)
        stats.pages += 1
        rows.extend(body["d"]["results"])
        url = body["d"].get("__next")
    stats.records, stats.retries = len(rows), client.retries - before
    return rows, stats


def sf_current_jobs(empjob: list[dict], as_of: date) -> dict[str, str]:
    """EmpJob is effective-dated: pick the record valid on `as_of`, highest seqNumber wins."""
    best: dict[str, tuple[int, str]] = {}
    for r in empjob:
        start, end = odata_date(r["startDate"]), odata_date(r["endDate"])
        if start <= as_of <= end:
            if r["userId"] not in best or r["seqNumber"] > best[r["userId"]][0]:
                best[r["userId"]] = (r["seqNumber"], r["jobCode"])
    return {u: code for u, (_, code) in best.items()}


def sf_people(users: list[dict], jobs: dict[str, str]) -> list[SourcePerson]:
    return [SourcePerson("successfactors", u["userId"], f"{u['firstName']} {u['lastName']}", u["firstName"], u["lastName"],
                         u.get("email"), odata_date(u.get("hireDate")), jobs.get(u["userId"]), None, u.get("country"),
                         u.get("status") == "active", {}, odata_date(u.get("lastModifiedDateTime")))
            for u in users]


def sf_jobs(rows: list[dict]) -> list[Job]:
    return [Job("successfactors", r["externalCode"], r["name"], r.get("description") or "", r.get("language"),
                odata_date(r.get("lastModifiedDateTime")), r.get("status") == "A") for r in rows]


def sf_about(rows: list[dict]) -> list[Activity]:
    return [Activity("successfactors", "about", f"about:{r['userId']}", f"successfactors:{r['userId']}", r["aboutMe"], None) for r in rows]


# ---------------------------------------------------------------------- Jira
def jira_issues(client: Client, jql: str, page_size: int = 100) -> tuple[list[dict], FetchStats]:
    stats = FetchStats("jira")
    before = client.retries
    out: list[dict] = []
    token: str | None = None
    while True:
        body = client.get_json("/jira/rest/api/3/search/jql",
                               {"jql": jql, "fields": ",".join(JIRA_FIELDS), "maxResults": page_size, "nextPageToken": token})
        stats.pages += 1
        out.extend(body["issues"])
        if body.get("isLast", True):
            break
        token = body["nextPageToken"]
    stats.records, stats.retries = len(out), client.retries - before
    return out, stats


def jira_users(client: Client, page_size: int = 50) -> list[SourcePerson]:
    out, start = [], 0
    while True:
        page = client.get_json("/jira/rest/api/3/users/search", {"startAt": start, "maxResults": page_size})
        out += [SourcePerson("jira", u["accountId"], u["displayName"], email=u.get("emailAddress"), active=u.get("active", True)) for u in page]
        if len(page) < page_size:
            return out
        start += page_size


def jira_activities(issues: list[dict]) -> list[Activity]:
    acts = []
    for i in issues:
        f = i["fields"]
        if not f.get("assignee"):
            continue
        acts.append(Activity("jira", "ticket", i["key"], f"jira:{f['assignee']['accountId']}", f["summary"], iso_date(f.get("resolutiondate"))))
    return acts


# ---------------------------------------------------------------------- files
def lms_completions(path: Path) -> list[Activity]:
    with path.open(encoding="utf-8", newline="") as fh:
        return [Activity("lms", "course", f"course:{r['course_id']}", f"lms:{r['learner_email'].lower()}", r["course_title"], iso_date(r["completed_on"]))
                for r in csv.DictReader(fh)]


def libraries(wd_entries: list[dict], sf_path: Path) -> list[LibrarySkill]:
    out = [LibrarySkill("workday", e["Skill_ID"], [e["Skill_Name"]]) for e in wd_entries]
    for r in json.loads(sf_path.read_text(encoding="utf-8")):
        out.append(LibrarySkill("successfactors", r["externalCode"], [n for n in (r.get("name_de_DE"), r.get("name_en_US")) if n]))
    return out


def optouts(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
