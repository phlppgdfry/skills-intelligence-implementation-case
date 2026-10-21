"""Local stand-ins for the customer's APIs, with the failure modes real tenants have.

One HTTP server answers three API shapes:

    /workday/ccx/api/v1/{tenant}/workers                 Workday REST: offset/limit, {"total", "data"}
    /workday/ccx/service/customreport2/{tenant}/...      Workday RaaS: {"Report_Entry": [...]}
    /sf/odata/v2/{Entity}                                SuccessFactors OData v2: {"d": {"results", "__next"}}
    /jira/rest/api/3/search/jql                          Jira Cloud: nextPageToken / isLast
    /jira/rest/api/3/users/search                        Jira Cloud: startAt / maxResults

With faults on, the server answers 429 (with Retry-After) or 503 once on chosen
pages, so the connectors' retry logic is exercised on every eval run.

The shapes follow the public API conventions; they are not copies of any
vendor's full schema.
"""

from __future__ import annotations

import json
import threading
import urllib.parse
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from ..config import SOURCES

TOKEN = "dev-token-not-a-secret"
SF_PAGE = 40
WD_MAX_LIMIT = 100


def _load(rel: str):
    return json.loads((SOURCES / rel).read_text(encoding="utf-8"))


@dataclass
class State:
    faults: bool = True
    workers: list = field(default_factory=lambda: _load("workday/workers.json"))
    job_profiles: dict = field(default_factory=lambda: _load("workday/job_profiles.json"))
    skills_library: dict = field(default_factory=lambda: _load("workday/skills_library.json"))
    sf: dict = field(default_factory=lambda: {
        "User": _load("successfactors/User.json"),
        "EmpJob": _load("successfactors/EmpJob.json"),
        "FOJobCode": _load("successfactors/FOJobCode.json"),
        "cust_AboutMe": _load("successfactors/cust_AboutMe.json"),
    })
    issues: list = field(default_factory=lambda: _load("jira/issues.json"))
    jira_users: list = field(default_factory=lambda: _load("jira/users.json"))
    requests: int = 0
    faults_served: list = field(default_factory=list)
    _fired: set = field(default_factory=set)

    def fault_once(self, key: str) -> bool:
        if not self.faults or key in self._fired:
            return False
        self._fired.add(key)
        self.faults_served.append(key)
        return True


class Handler(BaseHTTPRequestHandler):
    state: State

    def log_message(self, *args) -> None:  # keep test output clean
        pass

    def _send(self, status: int, body, headers: dict | None = None) -> None:
        raw = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802
        st = self.state
        st.requests += 1
        if self.headers.get("Authorization") != f"Bearer {TOKEN}":
            return self._send(401, {"error": "invalid_token"})
        url = urllib.parse.urlsplit(self.path)
        q = dict(urllib.parse.parse_qsl(url.query))
        parts = [p for p in url.path.split("/") if p]
        try:
            if parts[:4] == ["workday", "ccx", "api", "v1"] and parts[5:] == ["workers"]:
                return self._workers(q)
            if parts[:4] == ["workday", "ccx", "service", "customreport2"]:
                report = parts[-1]
                body = {"Job_Profiles_for_Skills_Layer": st.job_profiles, "Skills_Library": st.skills_library}.get(report)
                return self._send(200, body) if body else self._send(404, {"error": "report not found"})
            if parts[:3] == ["sf", "odata", "v2"]:
                return self._odata(parts[3], q)
            if parts[:5] == ["jira", "rest", "api", "3", "search"] and parts[5:] == ["jql"]:
                return self._jira_search(q)
            if parts[:5] == ["jira", "rest", "api", "3", "users"]:
                start, size = int(q.get("startAt", 0)), int(q.get("maxResults", 50))
                return self._send(200, st.jira_users[start:start + size])
        except (ValueError, KeyError) as e:
            return self._send(400, {"error": str(e)})
        return self._send(404, {"error": "not found"})

    def _workers(self, q: dict) -> None:
        st = self.state
        offset, limit = int(q.get("offset", 0)), int(q.get("limit", 20))
        if limit > WD_MAX_LIMIT:
            return self._send(400, {"error": f"limit must be <= {WD_MAX_LIMIT}"})
        rows = st.workers
        if "updatedFrom" in q:
            rows = [w for w in rows if w["lastUpdated"] >= q["updatedFrom"]]
        if offset == 100 and st.fault_once("workday:429@offset=100"):
            return self._send(429, {"error": "rate limited"}, {"Retry-After": "1"})
        self._send(200, {"total": len(rows), "data": rows[offset:offset + limit]})

    def _odata(self, entity: str, q: dict) -> None:
        st = self.state
        rows = st.sf[entity]
        skip = int(q.get("$skiptoken", 0))
        if skip == SF_PAGE and st.fault_once(f"sf:503@{entity}"):
            return self._send(503, {"error": {"message": {"value": "Service temporarily unavailable"}}})
        page = rows[skip:skip + SF_PAGE]
        body = {"d": {"results": page}}
        if skip + SF_PAGE < len(rows):
            base = f"http://{self.headers['Host']}/sf/odata/v2/{entity}"
            body["d"]["__next"] = f"{base}?$format=json&$skiptoken={skip + SF_PAGE}"
        self._send(200, body)

    def _jira_search(self, q: dict) -> None:
        st = self.state
        size = min(int(q.get("maxResults", 50)), 100)
        start = int(q.get("nextPageToken") or 0)
        if start == 300 and st.fault_once("jira:429@300"):
            return self._send(429, {"errorMessages": ["Rate limit exceeded"]}, {"Retry-After": "2"})
        rows = [i for i in st.issues if i["fields"]["status"]["name"] == "Done"] if "Done" in q.get("jql", "") else st.issues
        page = rows[start:start + size]
        fields = [f for f in q.get("fields", "").split(",") if f]
        if fields:  # only the fields asked for leave the tenant
            page = [{"key": i["key"], "fields": {f: i["fields"].get(f) for f in fields}} for i in page]
        last = start + size >= len(rows)
        body = {"issues": page, "isLast": last}
        if not last:
            body["nextPageToken"] = str(start + size)
        self._send(200, body)


class MockServer:
    """Run the mock APIs on a free localhost port, for tests, evals and the demo."""

    def __init__(self, faults: bool = True, port: int = 0) -> None:
        self.state = State(faults=faults)
        handler = type("BoundHandler", (Handler,), {"state": self.state})
        self.httpd = ThreadingHTTPServer(("127.0.0.1", port), handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.httpd.server_address[1]}"

    def __enter__(self) -> "MockServer":
        self.thread.start()
        return self

    def __exit__(self, *exc) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
