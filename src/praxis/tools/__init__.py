"""Business arithmetic and retrieval: independent of any LLM."""
from decimal import Decimal
from praxis.schemas import (Dataset, RecordResult, Metrics, DeadlineResult,
    DeadlineRisk, Escalation, EscalationResult, Event, Category,
    OperatingSnapshot, SnapshotMetrics, UpdateSummary)


class BusinessTools:
    def __init__(self, dataset: Dataset):
        self.dataset = dataset
        self.by_id = {r.record_id: r for r in dataset.records}
        self.events: list[Event] = []
        self.actor = 'Application'

    def record_event(self, name, result):
        self.events.append(Event(actor=self.actor, kind='tool', tool=name,
            source_ids=result.source_ids, detail='Completed successfully'))
        return result

    def get_operating_snapshot(self):
        records = self.get_business_updates()
        fields = set(UpdateSummary.model_fields)
        metrics = self.calculate_business_metrics()
        return self.record_event('get_operating_snapshot', OperatingSnapshot(
            reference_date=self.dataset.reference_date,
            updates=[UpdateSummary.model_validate(row.model_dump(include=fields)) for row in records.records],
            metrics=SnapshotMetrics.model_validate(metrics.model_dump(include=set(SnapshotMetrics.model_fields))),
            deadlines=self.get_deadline_risks(), policy=self.get_policy_escalations(),
            source_ids=records.source_ids))

    def get_business_updates(self, category: Category | None = None, status: str | None = None):
        if status not in (None, 'open', 'blocked', 'completed', 'cancelled'):
            raise ValueError('Unsupported status filter')
        rows = [r for r in self.dataset.records if (category is None or r.category == category)
                and (status is None or r.status == status)]
        return self.record_event('get_business_updates', RecordResult(records=rows, source_ids=[r.record_id for r in rows]))

    def get_record_details(self, record_id: str):
        if record_id not in self.by_id:
            raise ValueError('Unknown record ID')
        row = self.by_id[record_id]
        ids = list(dict.fromkeys([record_id] + row.related_record_ids))
        return self.record_event('get_record_details', RecordResult(records=[self.by_id[i] for i in ids], source_ids=ids))

    def calculate_business_metrics(self):
        active = [r for r in self.dataset.records if r.active]
        issue_categories = {'support', 'cancellation', 'product', 'operations', 'finance'}
        issues = [r for r in active if r.category in issue_categories]
        customers = [r for r in active if r.category in {'support', 'cancellation'}]
        overdue = [r for r in active if r.category in {'operations', 'product', 'finance'}
                   and r.deadline and r.deadline < self.dataset.reference_date]
        sales = [r for r in active if r.category == 'sales']
        contract_ids = {i for r in customers for i in r.related_record_ids
                        if self.by_id[i].category == 'contract' and self.by_id[i].active}
        contracts = [self.by_id[i] for i in sorted(contract_ids)]
        def totals(rows):
            result = {}
            for row in rows:
                if row.contract_value is not None:
                    result[row.currency] = result.get(row.currency, Decimal(0)) + row.contract_value
            return result
        missing = [r.record_id for r in sales + contracts if r.contract_value is None]
        missing += [r.record_id for r in customers if not any(i in contract_ids for i in r.related_record_ids)]
        cohorts = {name: [r.record_id for r in rows] for name, rows in
                   [('open_issues', issues), ('overdue_tasks', overdue), ('customer_escalations', customers),
                    ('opportunities_awaiting_action', sales), ('exposure', contracts)]}
        definitions = {
            'exposure': 'Sum of recorded face values of distinct active authoritative contracts directly linked to open/blocked support or cancellation records. Exposure, not expected loss or recognized revenue. Missing values excluded; grouped by currency.',
            'pipeline': 'Sum of recorded potential deal values on open/blocked sales records, grouped by currency. Not contracted or realized revenue.',
            'open_issues': 'Count of open/blocked support, cancellation, product, operations and finance records; one record per issue.',
            'overdue_tasks': 'Count of open/blocked operations, product and finance records with deadline strictly before the reference date.',
            'customer_escalations': 'Count of open/blocked support and cancellation records; not distinct customers.',
            'opportunities_awaiting_action': 'Count of open/blocked sales records. Each sales record represents one distinct opportunity.'}
        sources = sorted({i for ids in cohorts.values() for i in ids})
        return self.record_event('calculate_business_metrics', Metrics(reference_date=self.dataset.reference_date,
            exposure_by_currency=totals(contracts), pipeline_by_currency=totals(sales), open_issues=len(issues),
            overdue_tasks=len(overdue), customer_escalations=len(customers), opportunities_awaiting_action=len(sales),
            missing_financial_ids=sorted(set(missing)), source_ids=sources, cohorts=cohorts, definitions=definitions))

    def get_deadline_risks(self, window_days: int = 7):
        if not 0 <= window_days <= 90:
            raise ValueError('Window must be between zero and ninety days')
        risks = []
        for row in self.dataset.records:
            if row.active and row.deadline:
                days = (row.deadline - self.dataset.reference_date).days
                if days <= window_days:
                    risks.append(DeadlineRisk(record_id=row.record_id, deadline=row.deadline,
                        days_remaining=days, overdue=days < 0))
        risks.sort(key=lambda r: (r.days_remaining, r.record_id))
        return self.record_event('get_deadline_risks', DeadlineResult(reference_date=self.dataset.reference_date,
            window_days=window_days, risks=risks, source_ids=[r.record_id for r in risks]))

    def get_policy_escalations(self):
        escalations = []
        for row in self.dataset.records:
            if not (row.active and row.category == 'support' and row.severity == 'critical'):
                continue
            related = [self.by_id[i] for i in row.related_record_ids]
            imminent = [r for r in related if r.active and r.category == 'contract' and r.deadline
                        and (r.deadline - self.dataset.reference_date).days <= 7]
            if imminent:
                escalations.append(Escalation(record_id=row.record_id, rule='CRITICAL_SERVICE_RENEWAL',
                    reason='Unresolved critical service incident with contractual deadline due within seven days or overdue.',
                    source_ids=[row.record_id] + [r.record_id for r in imminent]))
        return self.record_event('get_policy_escalations', EscalationResult(escalations=escalations,
            source_ids=sorted({i for e in escalations for i in e.source_ids})))
