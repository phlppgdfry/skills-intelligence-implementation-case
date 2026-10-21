"""The validation moment: an Adaptive Card in Microsoft Teams that asks the employee to confirm.

The employee sees each suggested skill with the evidence behind it and answers
"yes", "no" or "not sure". Nothing is written to Workday or shown to a manager
until they do (ADR-0001). Slack gets the same content as Block Kit; the logic
does not change, only the rendering.
"""

from __future__ import annotations

from .inference import SkillScore
from .taxonomy import load

MAX_SKILLS = 6       # a card people answer, not a card people scroll
EVIDENCE_CHARS = 90


def validation_card(first_name: str, suggestions: list[SkillScore], run_id: str) -> dict:
    tax = load().by_id
    body: list[dict] = [
        {"type": "TextBlock", "size": "Medium", "weight": "Bolder", "text": f"Hi {first_name}, are these your skills?"},
        {"type": "TextBlock", "wrap": True, "isSubtle": True,
         "text": "We found these in your work. Only what you confirm is added to your Workday profile. You can change it any time."},
    ]
    for s in suggestions[:MAX_SKILLS]:
        ev = s.evidence[0]
        where = {"job": "your job profile", "ticket": f"Jira {ev.ref}", "course": "a course you completed", "about": "your profile text"}[ev.kind]
        quote = ev.sentence if len(ev.sentence) <= EVIDENCE_CHARS else ev.sentence[: EVIDENCE_CHARS - 1] + "…"
        body += [
            {"type": "TextBlock", "weight": "Bolder", "text": tax[s.skill_id].name, "spacing": "Medium"},
            {"type": "TextBlock", "wrap": True, "isSubtle": True, "size": "Small",
             "text": f"From {where}: “{quote}”" + (f" (+{len(s.evidence) - 1} more)" if len(s.evidence) > 1 else "")},
            {"type": "Input.ChoiceSet", "id": f"skill:{s.skill_id}", "style": "expanded", "value": "unsure",
             "choices": [{"title": "Yes, that's me", "value": "accept"}, {"title": "No", "value": "reject"}, {"title": "Not sure", "value": "unsure"}]},
        ]
    return {
        "type": "AdaptiveCard", "$schema": "http://adaptivecards.io/schemas/adaptive-card.json", "version": "1.5",
        "body": body,
        "actions": [{"type": "Action.Execute", "title": "Send", "verb": "validateSkills", "data": {"run": run_id}}],
    }
