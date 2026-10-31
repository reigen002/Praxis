"""Reject unverifiable references and numeric prose before display."""
import re
from praxis.schemas import Analysis, Briefing
from praxis.tools import BusinessTools


class OutputRejected(ValueError):
    pass


def check_prose(text: str, valid_ids=()):
    # Numeric facts belong in deterministic metrics/evidence, never generated prose.
    # This conservative lexical check is not a semantic entailment verifier.
    identifiers = re.findall(r'\b[A-Z]+-\d{3}\b', text)
    if set(identifiers) - set(valid_ids):
        raise OutputRejected(f'Unknown record identifier in prose: {sorted(set(identifiers) - set(valid_ids))}. '
            f'Allowed record IDs for this claim: {sorted(set(valid_ids))}')
    text = re.sub(r'\b[A-Z]+-\d{3}\b', '', text)
    numeric = r'\d|[$€£₹%]|\b(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|million|billion|trillion|percent)\b'
    match = re.search(numeric, text, flags=re.IGNORECASE)
    if match:
        raise OutputRejected(f'Remove numeric token {match.group()!r} from prose; use qualitative wording. Numeric facts belong in deterministic metrics/evidence.')


def check_sources(record_id, source_ids, tools, *, related_only=True):
    if record_id not in tools.by_id or record_id not in source_ids:
        raise OutputRejected(f'Primary record must exist and be cited: record_id={record_id!r}, '
            f'source_ids={source_ids!r}. Use an exact record ID and include it in its own source_ids.')
    allowed = {record_id, *tools.by_id[record_id].related_record_ids} if related_only else set(tools.by_id)
    invalid = set(source_ids) - allowed
    if invalid:
        raise OutputRejected(f'Invalid or unrelated source reference for {record_id}: {sorted(invalid)}. '
            f'Allowed source_ids for this item: {sorted(allowed)}')


def validate_analysis(analysis: Analysis, tools: BusinessTools):
    retrieved = {i for e in tools.events if e.actor == 'Business Operations Analyst'
        and e.tool in ('get_business_updates', 'get_record_details') for i in e.source_ids}
    if not retrieved:
        raise OutputRejected('Analyst must execute a genuine retrieval tool')
    for finding in analysis.findings:
        # Analyst comparisons may span unlinked records; each must have been retrieved.
        check_sources(finding.record_id, finding.source_ids, tools, related_only=False)
        if set(finding.source_ids) - retrieved:
            raise OutputRejected('Finding cites evidence not retrieved by analyst')
        check_prose(' '.join([finding.observation, *finding.assumptions]), finding.source_ids)
    # Global limitations may discuss retrieved evidence omitted from individual findings.
    check_prose(' '.join(analysis.limitations), retrieved)
    return analysis


def validate_briefing(briefing: Briefing, tools: BusinessTools, analysis: Analysis | None = None):
    analyzed = {i for f in analysis.findings for i in f.source_ids} if analysis else {
        i for item in [*briefing.priorities, *briefing.follow_ups] for i in item.source_ids}
    global_evidence = set(analyzed)
    if analysis:
        # Validated global limitations can cite retrieved records outside findings.
        # Carry that evidence into summary/limitations, not priority eligibility.
        retrieved = {i for e in tools.events if e.actor == 'Business Operations Analyst'
            and e.tool in ('get_business_updates', 'get_record_details') for i in e.source_ids}
        limitation_ids = set(re.findall(r'\b[A-Z]+-\d{3}\b', ' '.join(analysis.limitations)))
        global_evidence |= limitation_ids & retrieved & set(tools.by_id)
    check_prose(' '.join([briefing.executive_summary, *briefing.data_limitations]), global_evidence)
    ids = [p.record_id for p in briefing.priorities]
    if len(ids) != len(set(ids)):
        raise OutputRejected('Duplicate priorities')
    if [p.rank for p in briefing.priorities] != list(range(1, len(ids) + 1)):
        raise OutputRejected('Ranks must be consecutive and ordered')
    for priority in briefing.priorities:
        check_sources(priority.record_id, priority.source_ids, tools)
        if set(priority.source_ids) - analyzed:
            raise OutputRejected('Priority lacks validated analyst evidence')
        row = tools.by_id[priority.record_id]
        if not row.active:
            raise OutputRejected(f'Record {priority.record_id} is {row.status} and cannot be an active priority')
        if row.category != priority.category:
            raise OutputRejected(f'Incorrect source category for {priority.record_id}: expected {row.category}, received {priority.category}')
        check_prose(' '.join([priority.title, priority.business_impact, priority.recommended_action, *priority.assumptions]), priority.source_ids)
    previous_actor = tools.actor
    try:
        tools.actor = 'Output validation'
        mandatory = tools.get_policy_escalations().escalations
    finally:
        tools.actor = previous_actor
    for escalation in mandatory:
        matches = [p for p in briefing.priorities if p.record_id == escalation.record_id]
        if not matches or matches[0].urgency != 'Critical' or matches[0].rank > len(mandatory):
            raise OutputRejected('Mandatory escalation must lead priorities at Critical urgency')
        if set(escalation.source_ids) - set(matches[0].source_ids):
            raise OutputRejected('Mandatory escalation requires contractual evidence')
    for draft in briefing.follow_ups:
        check_sources(draft.record_id, draft.source_ids, tools)
        if draft.record_id not in ids or set(draft.source_ids) - analyzed:
            raise OutputRejected('Follow-up must refer to an evidenced priority')
        check_prose(draft.draft, draft.source_ids)
    return briefing
