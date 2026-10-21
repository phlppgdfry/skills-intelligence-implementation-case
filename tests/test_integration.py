"""Integration tests: real HTTP against the mock tenants, and the whole pipeline."""

from __future__ import annotations

import unittest

from skillslayer import pipeline
from skillslayer.landscape import TENANT, fetch
from skillslayer.mock.servers import TOKEN, MockServer
from skillslayer.sources import connectors as c
from skillslayer.sources.http import ApiError, Client


class Http(unittest.TestCase):
    def test_retries_429_and_503_then_completes(self):
        with MockServer(faults=True) as m:
            land = fetch(m.url, TOKEN)
            self.assertEqual(len(land.workday), len(m.state.workers))
            self.assertEqual(len(land.jira) and sum(1 for a in land.activities if a.kind == "ticket"), len(m.state.issues))
            self.assertEqual(land.retries, len(m.state.faults_served))

    def test_4xx_is_not_retried(self):
        with MockServer() as m:
            client = Client(m.url, TOKEN, time_scale=0.01)
            with self.assertRaises(ApiError) as e:
                client.get_json(f"/workday/ccx/api/v1/{TENANT}/workers", {"limit": 500})
            self.assertEqual(e.exception.status, 400)
            self.assertEqual(len(client.log), 1)

    def test_jira_only_returns_requested_fields(self):
        with MockServer(faults=False) as m:
            issues, _ = c.jira_issues(Client(m.url, TOKEN), "statusCategory = Done")
        self.assertTrue(all(set(i["fields"]) <= set(c.JIRA_FIELDS) for i in issues))


class Pipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with MockServer(faults=False) as m:
            cls.land = fetch(m.url, TOKEN)
        cls.r = pipeline.run(cls.land)

    def test_opted_out_people_have_no_evidence(self):
        self.assertTrue(self.r.excluded)
        for eid in self.r.excluded:
            self.assertNotIn(eid, self.r.evidence)

    def test_quarantined_text_never_becomes_evidence(self):
        q = set(self.r.ready["quarantined"])
        self.assertTrue(q)
        self.assertFalse(any(e.ref in q for evs in self.r.evidence.values() for e in evs))

    def test_nothing_is_written_without_validation(self):
        self.assertEqual(self.r.ops, [])
        self.assertEqual(self.r.export_rows, [])

    def test_every_suggestion_carries_evidence(self):
        for sugg in self.r.suggested.values():
            for s in sugg:
                self.assertTrue(s.evidence and all(e.sentence for e in s.evidence))


if __name__ == "__main__":
    unittest.main()
