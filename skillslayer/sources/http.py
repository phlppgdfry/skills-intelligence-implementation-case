"""A small, honest HTTP client for HR and work-system APIs.

Real HR APIs fail in boring ways: 429 with Retry-After, a 503 during a tenant
maintenance window, a page that times out. The client retries those, backs off
exponentially with deterministic jitter, and never retries a 4xx that means
"your request is wrong" (400, 401, 403, 404). Every attempt is logged so the
run report can show what happened.
"""

from __future__ import annotations

import json
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field

RETRYABLE = {429, 500, 502, 503, 504}


class ApiError(Exception):
    def __init__(self, status: int, url: str, body: str = "") -> None:
        super().__init__(f"HTTP {status} for {url}: {body[:200]}")
        self.status = status


@dataclass
class Attempt:
    url: str
    status: int
    waited: float


@dataclass
class Client:
    base_url: str
    token: str | None = None
    max_retries: int = 5
    base_delay: float = 0.5
    time_scale: float = 1.0      # tests and evals shrink waits; production keeps 1.0
    timeout: float = 30.0
    log: list[Attempt] = field(default_factory=list)
    seed: int = 7

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)

    def get_json(self, path_or_url: str, params: dict | None = None) -> dict | list:
        url = path_or_url if path_or_url.startswith("http") else self.base_url.rstrip("/") + "/" + path_or_url.lstrip("/")
        if params:
            q = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
            url += ("&" if "?" in url else "?") + q
        for attempt in range(self.max_retries + 1):
            req = urllib.request.Request(url, headers={"Accept": "application/json",
                                                       **({"Authorization": f"Bearer {self.token}"} if self.token else {})})
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    self.log.append(Attempt(url, resp.status, 0.0))
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", "replace")
                e.close()
                if e.code not in RETRYABLE or attempt == self.max_retries:
                    self.log.append(Attempt(url, e.code, 0.0))
                    raise ApiError(e.code, url, body) from None
                wait = self._wait(attempt, e.headers.get("Retry-After"))
                self.log.append(Attempt(url, e.code, wait))
                time.sleep(wait * self.time_scale)
        raise AssertionError("unreachable")

    def _wait(self, attempt: int, retry_after: str | None) -> float:
        if retry_after and retry_after.isdigit():
            return float(retry_after)
        return self.base_delay * (2 ** attempt) * (0.5 + self._rng.random() / 2)

    @property
    def retries(self) -> int:
        return sum(1 for a in self.log if a.status in RETRYABLE)

