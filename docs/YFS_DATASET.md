# Young Founders School-inspired demonstration data

**SYNTHETIC DEMONSTRATION DATA.** This is an invented operating day, informed by
public programme descriptions. It is not Young Founders School's internal data,
an endorsement, or a report of actual incidents. Research checked the school,
internship, mentor, corporate and donor pages; [research notes](YOUNG_FOUNDER_RESEARCH.md)
separate those public facts from inferred operational needs.

## Default scenario

`data/synthetic/yfs_operations.json` contains 28 linked records at a fixed
reference date of **30 October 2026**. The founder needs to get a fictional
internship cohort ready, resolve a school access issue before a renewal review,
confirm mentors and project briefs, respond to proposals, and validate sponsor
reporting. The dates are independent of the computer's current date.

| Founder question | Evidence |
|---|---|
| Can the next cohort start with usable onboarding access? | INC-001, CON-001, NOTE-001, NOTE-002 |
| Are mentors and host project briefs ready? | INC-002, OPS-001, OPS-002, OPS-004 |
| Is an existing partner relationship at risk? | CAN-001, CON-002; CAN-002 lacks agreement evidence |
| Which proposed partnerships need a response? | SALE-001, SALE-002, SALE-003 |
| What blocks the onboarding workflow release? | REL-001, OPS-004 |
| Can we substantiate a sponsor impact report? | FIN-001, NOTE-003; registrations must not be called verified completions |
| What can wait? | FEAT-001 certificate preview redesign, UPD-001 newsletter, DEV-001 fictional pilot discovery |
| Which historical items must stay closed? | DONE-001 completed export fix; DONE-002 cancelled proposal |

Every source is labeled Synthetic. School/host/sponsor names, agreements, amounts,
dates, communications and problems are invented. No identifiable students, real
emails, or private donor information are present. INR provides one consistent
demo currency; it is not a claim about YFS's actual contracting or reporting
currency. Standard owner labels such as Customer Success and Sales represent
suggested partner-support and partnership responsibilities, not a real YFS org chart.

## Financial and operational definitions

| Measure | Verified value | Eligibility |
|---|---:|---|
| Programme agreement exposure | INR 300,000.00 | Distinct active signed contracts CON-001 (180,000) and CON-002 (120,000), linked to unresolved support/cancellation concerns |
| Potential partnership pipeline | INR 340,000.00 | Active proposals SALE-001 (250,000) and SALE-002 (90,000); SALE-003 has unknown value |
| Open issues | 13 | Open/blocked support, cancellation, product, operations and finance records |
| Overdue internal tasks | 3 | Open/blocked operations, product or finance tasks with deadline strictly before the reference date: OPS-002, OPS-003, FIN-001 |
| School or sponsor issue records | 4 | Active support/cancellation records INC-001, INC-002, CAN-001 and CAN-002; not four distinct partners |
| Proposals awaiting action | 3 | All active sales-category proposals, including the unvalued SALE-003 |

These are counts or sums over stated cohorts, not rates with implied student or
partner denominators. A deadline on the reference date is approaching, not overdue.
Missing finance remains unknown for CAN-002 and SALE-003. The cancelled proposal
is excluded. Exposure is face value, not expected loss, recognized revenue or
cash received. Proposals are unsigned possibilities, not donations or committed
funding. The source drawer exposes the exact eligibility and record IDs.

INC-001 is unresolved and critical with an approaching contractual deadline on
CON-001, so mandatory policy requires it to lead at Critical. The administrative
access check and learner-role failure conflict; recovery is not established.
The sources do not establish a contractual requirement to restore access as a
condition of renewal. FEAT-001 has no deadline or contractual commitment. Model
recommendations still require human review even when references are valid.

## Reproducibility and limited JEV usage

React, API defaults and CLI use this seed. The original startup demo remains
selectable and unchanged; its genuine saved JEV response remains tied to its own
evidence. Cache fingerprints include complete record/related evidence, date,
questions and model, so identical IDs across datasets do not reuse decisions.
YFS has no live JEV evaluation in this revision; Rules preserves the allowance.
Changing datasets also resets the UI provider to Rules.

`yfs_evaluation.json` has ten labeled team-routing and urgency regression cases.
The rules informed these labels; this is not independent accuracy measurement.
`tests/test_yfs_data.py` checks the seed, exact metrics, mandatory/routine cases,
labels, API defaults, legacy preservation and cache separation. The existing
parser/metric/policy suites cover duplicates, invalid dates, missing values and
boundary cases. Live provider verification is reported separately in
[VERIFICATION.md](VERIFICATION.md).

Try the morning briefing, then: “Why is the cohort access issue more urgent than
the certificate preview redesign?” Open INC-001/CON-001 and FEAT-001 to compare
the sources. Inspect a proposed follow-up and approve or reject locally; this
never contacts schools, mentors or students.
