"""Unit tests: each building block on its own, with small hand-written inputs."""

from __future__ import annotations

import unittest
from datetime import date

from skillslayer import inference, writeback
from skillslayer.canonical import LibrarySkill, ProfileSkill, SourcePerson
from skillslayer.crosswalk import map_library
from skillslayer.identity import fold, resolve
from skillslayer.inference import Evidence
from skillslayer.sources.connectors import odata_date, sf_current_jobs
from skillslayer.teams import validation_card


class Extraction(unittest.TestCase):
    def test_alias_in_four_languages(self):
        for text in ("Kennis van hoogspanning is vereist.", "Erfahrung mit Hochspannung.", "Experience with high voltage.",
                     "Une expérience en haute tension."):
            self.assertEqual(inference.skills_in(text, "C"), {"SK-001"}, text)

    def test_config_a_only_knows_canonical_names(self):
        self.assertEqual(inference.skills_in("Erfahrung mit Hochspannung.", "A"), set())
        self.assertEqual(inference.skills_in("Experience with Python.", "A"), {"SK-015"})

    def test_longest_form_wins(self):
        self.assertEqual(inference.skills_in("We build services in Spring Boot.", "C"), {"SK-017"})

    def test_negation_and_aspiration_are_not_skills(self):
        self.assertEqual(inference.skills_in("No experience with Docker is needed.", "C"), set())
        self.assertEqual(inference.skills_in("Ich möchte Kubernetes lernen.", "C"), set())
        self.assertEqual(inference.skills_in("No experience with Docker is needed.", "B"), {"SK-023"})

    def test_ambiguous_word_needs_context(self):
        self.assertEqual(inference.skills_in("You excel at keeping deadlines.", "C"), set())
        self.assertEqual(inference.skills_in("Advanced Excel with pivot tables and formulas.", "C"), {"SK-030"})
        self.assertEqual(inference.skills_in("We keep the team lean.", "C"), set())
        self.assertEqual(inference.skills_in("Lean in production: kaizen every week.", "C"), {"SK-034"})

    def test_mention_keeps_its_sentence_as_evidence(self):
        m = inference.extract("Intro. You will work daily with SCADA. Outro.", "C")[0]
        self.assertEqual(m.sentence, "You will work daily with SCADA.")

    def test_known_limit_trailing_negation(self):
        # documented in docs/07-product-feedback: negation after the mention is not handled yet
        self.assertEqual(inference.skills_in("Python is not part of this role.", "C"), {"SK-015"})


class Fusion(unittest.TestCase):
    def test_noisy_or_and_decay(self):
        evs = [Evidence("SK-015", "job", "JP-1", "", None), Evidence("SK-015", "ticket", "T-1", "", date(2026, 9, 1))]
        p = inference.profile(evs, as_of=date(2026, 10, 1))
        self.assertGreater(p["SK-015"].score, 0.35)
        self.assertLess(p["SK-015"].score, 1)
        self.assertEqual(p["SK-015"].evidence[0].kind, "ticket")

    def test_job_alone_is_not_enough_by_default(self):
        p = inference.profile([Evidence("SK-015", "job", "JP-1", "", None)])
        self.assertEqual(inference.suggestions(p), [])
        p = inference.profile([Evidence("SK-015", "job", "JP-1", "", None)], weights=inference.BROAD_WEIGHTS)
        self.assertEqual(len(inference.suggestions(p)), 1)

    def test_old_evidence_is_ignored(self):
        p = inference.profile([Evidence("SK-015", "ticket", "T-1", "", date(2020, 1, 1))], as_of=date(2026, 10, 1))
        self.assertEqual(p, {})


class Connectors(unittest.TestCase):
    def test_odata_dates(self):
        self.assertEqual(odata_date("/Date(1704067200000)/"), date(2024, 1, 1))
        self.assertEqual(odata_date("/Date(1704067200000+0000)/"), date(2024, 1, 1))
        self.assertEqual(odata_date("/Date(253402214400000)/"), date.max)
        with self.assertRaises(ValueError):
            odata_date("2024-01-01")

    def test_effective_dated_job(self):
        rows = [
            {"userId": "u1", "seqNumber": 1, "startDate": "/Date(1577836800000)/", "endDate": "/Date(1704067199000)/", "jobCode": "OLD"},
            {"userId": "u1", "seqNumber": 2, "startDate": "/Date(1704067200000)/", "endDate": "/Date(253402214400000)/", "jobCode": "NEW"},
        ]
        self.assertEqual(sf_current_jobs(rows, date(2026, 1, 1)), {"u1": "NEW"})
        self.assertEqual(sf_current_jobs(rows, date(2022, 1, 1)), {"u1": "OLD"})


class Identity(unittest.TestCase):
    def test_fold(self):
        self.assertEqual(fold("Jürgen  Müller"), fold("Juergen Mueller"))
        self.assertEqual(fold("Chloé Van-Damme"), "chloe van damme")

    def test_homonym_goes_to_review_not_merged(self):
        wd = [SourcePerson("workday", "W1", "Thomas Becker", "Thomas", "Becker", "thomas.becker@norvane.example", date(2019, 3, 1))]
        sf = [SourcePerson("successfactors", "kd1", "Thomas Becker", "Thomas", "Becker", "thomas.becker@keldorf.example", date(2015, 1, 1))]
        res = resolve(wd, sf, [], [])
        self.assertNotEqual(res.of["workday:W1"], res.of["successfactors:kd1"])
        self.assertEqual(len(res.review), 1)

    def test_transfer_after_merger_is_linked(self):
        wd = [SourcePerson("workday", "W1", "Juergen Mueller", "Juergen", "Mueller", "juergen.mueller@norvane.example", date(2025, 9, 1))]
        sf = [SourcePerson("successfactors", "kd1", "Jürgen Müller", "Jürgen", "Müller", "juergen.mueller@keldorf.example", date(2012, 1, 1))]
        res = resolve(wd, sf, [], [])
        self.assertEqual(res.of["workday:W1"], res.of["successfactors:kd1"])

    def test_jira_initials_need_a_steward(self):
        wd = [SourcePerson("workday", "W1", "Anna Koch", "Anna", "Koch", "anna.koch@norvane.example", date(2020, 1, 1))]
        res = resolve(wd, [], [SourcePerson("jira", "acc1", "A. Koch")], [])
        self.assertNotIn("jira:acc1", res.of)
        self.assertEqual(res.review[0]["reason"], "initials only")


class Crosswalk(unittest.TestCase):
    def test_methods(self):
        maps = map_library([
            LibrarySkill("workday", "1", ["Python"]), LibrarySkill("workday", "2", ["Python (advanced)"]),
            LibrarySkill("workday", "3", ["Teamwork"]), LibrarySkill("successfactors", "4", ["Schweißen"]),
        ])
        self.assertEqual([(m.skill_id, m.method) for m in maps],
                         [("SK-015", "exact"), ("SK-015", "normalized"), (None, "none"), ("SK-012", "exact")])


class WriteBack(unittest.TestCase):
    names = {"SK-015": "Python", "SK-023": "Docker", "SK-018": "SQL"}

    def test_plan_is_idempotent_and_leaves_employee_skills_alone(self):
        current = [ProfileSkill("W1", "Python", None, "employee"), ProfileSkill("W1", "Docker", "SK-023", "skills-layer")]
        ops = writeback.plan({"W1": {"SK-015", "SK-018"}}, {"W1": {"SK-023"}}, current, self.names, "v1")
        self.assertEqual([(o.op, o.skill_id) for o in ops], [("add", "SK-018"), ("remove", "SK-023")])
        t = writeback.Target(current)
        t.apply(ops)
        t.apply(ops)
        self.assertEqual(t.applied, 2)
        self.assertEqual(t.replayed, 2)
        self.assertIn(ProfileSkill("W1", "Python", None, "employee"), t.rows)
        self.assertEqual(writeback.plan({"W1": {"SK-015", "SK-018"}}, {"W1": {"SK-023"}}, t.rows, self.names, "v1"), [])

    def test_never_removes_what_an_employee_typed(self):
        current = [ProfileSkill("W1", "Docker", "SK-023", "employee")]
        self.assertEqual(writeback.plan({}, {"W1": {"SK-023"}}, current, self.names, "v1"), [])


class Card(unittest.TestCase):
    def test_card_shows_evidence_and_caps_length(self):
        scores = [inference.SkillScore(f"SK-0{10 + i}", 0.8, [Evidence(f"SK-0{10 + i}", "ticket", f"ELEC-{i}", "x" * 200, None)]) for i in range(9)]
        card = validation_card("Anna", scores, "r1")
        inputs = [b for b in card["body"] if b["type"] == "Input.ChoiceSet"]
        self.assertEqual(len(inputs), 6)
        self.assertTrue(any("Jira ELEC-0" in b.get("text", "") and "…" in b["text"] for b in card["body"]))
        self.assertEqual(card["actions"][0]["type"], "Action.Execute")


if __name__ == "__main__":
    unittest.main()
