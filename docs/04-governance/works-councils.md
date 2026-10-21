# Works councils: Belgium, Germany (and the Netherlands for wave 2)

*Working notes for employee relations. Not legal advice; Norvane's labour lawyers confirm each step.*

A skills platform touches what employee representatives care about most: being watched, being ranked, and losing control over your own story. Treat the councils as co-designers from week 1, not as a sign-off at the end. In Germany it is not optional.

## Belgium (Norvane)

| Instrument | What it requires | What we do |
|---|---|---|
| **CAO nr. 39** (introduction of new technologies) | in companies with 50+ employees, inform and consult the works council about a new technology with important collective consequences for employment, work organisation or working conditions, before it is introduced | information session in week 2; written information on purpose, data, effects and safeguards; consultation before the pilot |
| **CAO nr. 81** (control of electronic online communication data) | monitoring of electronic communication only for listed purposes, proportionate and transparent, with information to the council | we do **not** read communication content ([ADR-0002](../02-decisions/ADR-0002-work-metadata-not-message-content.md)); Jira metadata of finished work is explained explicitly so nobody has to assume |
| Work rules / ICT policy | changes to how employee data is used may need an update | HR checks whether the ICT policy needs a paragraph |

## Germany (Keldorf)

| Instrument | What it requires | What we do |
|---|---|---|
| **BetrVG §87(1) no. 6** | co-determination over the introduction and use of technical devices that are *suitable* to monitor behaviour or performance. Suitability is enough; the intent does not matter | a **works agreement** (*Betriebsvereinbarung*) before production data flows. It lists the data sources and fields, the purposes, who sees what, the retention, a ban on performance evaluation and the employee's rights |
| §90, §80(2) | information about planned technical systems; the council may call in an expert, which is common for AI | we budget the time for an external expert and give them access to this documentation |
| §95 | selection guidelines need agreement | the mobility matching is described as input for a conversation, not a selection guideline; legal confirms |

## Netherlands (wave 2, Norvane NL sites)

WOR art. 27(1)(l): the *ondernemingsraad* has a right of consent for arrangements on systems that can observe or check attendance, behaviour or performance. The same pack is reused.

## What goes into the agreement (proposed content)

1. **Purposes:** internal mobility, workforce planning, personal development. **Not** performance evaluation, discipline or dismissal decisions.
2. **Sources and fields:** the interface list with fields ([interface specs](../01-architecture/interface-specs.md)). No message content.
3. **Employee control:** validation before use; reject at any time; opt-out.
4. **Visibility:** managers see validated skills of their team; no "skills scores" or rankings; aggregate reports only for groups of 10 or more.
5. **Changes:** a new source or purpose means a new consultation.
6. **Review:** a joint review after 6 months, with the governance numbers from the run log.

## The demo that helps most

Show the council the **Teams validation card** for a fictional employee (`python -m skillslayer card W30579`). Point out that every suggestion says where it came from, that "No" is a full answer, and that nothing happens until the employee answers. It turns an abstract worry ("the AI judges me") into something concrete the council can test themselves.
