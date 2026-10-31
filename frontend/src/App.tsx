import { useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { Activity, ArrowDownToLine, ArrowRight, ArrowUpRight, BookOpen, Check, CheckCheck,
  ChevronRight, CircleAlert, Clock3, Copy, Database, FileText, FlaskConical, Info,
  LayoutDashboard, LoaderCircle, Menu, MessageSquareText, Search, ShieldCheck, Sparkles, X } from 'lucide-react'
import { api, ApiError } from './api'
import SavedBriefings from './SavedBriefings'
import type { SavedRun } from './SavedBriefings'
import { dateLabel, dueLabel, initials, money } from './format'
import type { BusinessRecord, DecisionComparison, Event, Job, Overview, Priority, RunResult } from './types'

const MORNING = 'Prepare my founder briefing for today. What are the three most important issues, and why?'
const EXPLAIN = 'Why is the customer renewal issue more urgent than the feature request?'
type Page = 'overview' | 'updates' | 'followups' | 'decisions' | 'activity'
type Drawer = { kind: 'record'; id: string } | { kind: 'metrics' } | null
type Review = 'approved' | 'rejected'
const nav = [{ id: 'overview', label: 'Overview', icon: LayoutDashboard }, { id: 'updates', label: 'Business updates', icon: Database },
  { id: 'followups', label: 'Follow-up review', icon: MessageSquareText }, { id: 'decisions', label: 'Decision lab', icon: FlaskConical },
  { id: 'activity', label: 'Execution activity', icon: Activity }] as const

function Badge({ children, tone = 'neutral' }: { children: ReactNode; tone?: string }) {
  return <span className={`badge ${tone}`}><span className="badge-dot" />{children}</span>
}
function urgencyTone(value: string) { return value === 'Critical' ? 'critical' : value === 'Time Sensitive' ? 'attention' : 'neutral' }
function elapsedLabel(seconds: number) { return `${Math.floor(seconds / 60).toString().padStart(2, '0')}:${Math.floor(seconds % 60).toString().padStart(2, '0')}` }
function download(result: RunResult) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' }))
  const link = document.createElement('a'); link.href = url; link.download = 'praxis-briefing.json'; link.click(); URL.revokeObjectURL(url)
}

export default function App() {
  const [page, setPage] = useState<Page>('overview')
  const [dataset, setDataset] = useState('yfs')
  const [overview, setOverview] = useState<Overview | null>(null)
  const [question, setQuestion] = useState(MORNING)
  const [decisionProvider, setDecisionProvider] = useState('rules')
  const [job, setJob] = useState<Job | null>(null)
  const [result, setResult] = useState<RunResult | null>(null)
  const [savedAt, setSavedAt] = useState<string | null>(null)
  const [reviews, setReviews] = useState<Record<string, Review>>({})
  const [error, setError] = useState('')
  const [reload, setReload] = useState(0)
  const [drawer, setDrawer] = useState<Drawer>(null)
  const [menuOpen, setMenuOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [status, setStatus] = useState('all')
  const [category, setCategory] = useState('all')
  const [elapsed, setElapsed] = useState(0)
  const [runStarted, setRunStarted] = useState(0)
  const [comparison, setComparison] = useState<DecisionComparison | null>(null)
  const [decisionRecord, setDecisionRecord] = useState('INC-001')
  const [evaluating, setEvaluating] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [copied, setCopied] = useState<number | null>(null)
  const menuButton = useRef<HTMLButtonElement>(null)
  const dialog = useRef<HTMLDialogElement>(null)
  const busy = job?.status === 'queued' || job?.status === 'running'

  useEffect(() => {
    const abort = new AbortController()
    setOverview(null); setError(''); setResult(null); setSavedAt(null); setJob(null); setReviews({}); setDrawer(null); setComparison(null)
    setQuestion(MORNING); setDecisionProvider('rules'); setDecisionRecord('INC-001')
    setQuery(''); setStatus('all'); setCategory('all')
    api<Overview>(`/overview?dataset=${encodeURIComponent(dataset)}`, { signal: abort.signal })
      .then(setOverview).catch(error => { if (error.name !== 'AbortError') setError('The workspace could not connect to the Python API. Start the backend on port 8000, then retry.') })
    return () => abort.abort()
  }, [dataset, reload])

  useEffect(() => {
    if (!job || !busy) return
    let active = true
    let failures = 0
    const poll = window.setInterval(() => {
      api<Job>(`/runs/${job.id}`).then(next => {
        if (!active) return
        if (failures) { setError(''); failures = 0 }
        setJob(next)
        if (next.status === 'completed' && next.result) { setResult(next.result); setReviews({}); setSavedAt(null); if (next.save_warning) setError(next.save_warning) }
        if (next.status === 'failed') setError(next.error || 'The briefing did not pass validation. Please retry.')
      }).catch(error => { if (active) {
        if (error instanceof ApiError && error.status === 404) { setError(error.message); setJob(null) }
        else { failures++; setError('The connection to this run was interrupted. Keeping the run ID and checking again; no new briefing is being started.') }
      } })
    }, 2000)
    const clock = window.setInterval(() => setElapsed((Date.now() - runStarted) / 1000), 1000)
    return () => { active = false; clearInterval(poll); clearInterval(clock) }
  }, [job?.id, busy, runStarted])

  useEffect(() => {
    const node = dialog.current
    if (drawer && node && !node.open) node.showModal()
    if (!drawer && node?.open) node.close()
  }, [drawer])

  async function generate() {
    setSubmitting(true)
    setError(''); setResult(null); setSavedAt(null); setReviews({}); setPage('overview'); setRunStarted(Date.now()); setElapsed(0)
    try {
      const started = await api<Job>('/runs', { method: 'POST', body: JSON.stringify({ question, dataset,
        decision_provider: decisionProvider, jev_record_id: decisionRecord }) })
      setJob(started)
      if (started.status === 'completed' && started.result) setResult(started.result)
    } catch (error) { setError(error instanceof Error ? error.message : 'Could not start the briefing.') }
    finally { setSubmitting(false) }
  }

  function openSaved(saved: SavedRun) {
    setResult(saved.result); setSavedAt(saved.result.events.at(-1)?.timestamp || saved.saved_at)
    setQuestion(saved.result.question); setReviews({}); setJob(null); setError(''); setPage('overview')
    setDecisionProvider(saved.result.decisions.some(decision => decision.provider === 'jev-ai.org') ? 'jev' : 'rules')
  }

  async function evaluate() {
    setError(''); setEvaluating(true)
    try {
      const next = overview?.readiness.jev.cached_record_id === decisionRecord
        ? await api<DecisionComparison>(`/decisions/cached?dataset=${encodeURIComponent(dataset)}&record_id=${encodeURIComponent(decisionRecord)}`)
        : await api<DecisionComparison>('/decisions/evaluate', { method: 'POST', body: JSON.stringify({ dataset, record_id: decisionRecord }) })
      setComparison(next)
      setOverview(current => current ? { ...current, readiness: { ...current.readiness, jev: {
        ...current.readiness.jev, live_verified: true, cached_record_id: decisionRecord } } } : current)
    } catch (error) { setError(error instanceof Error ? error.message : 'JEV could not evaluate this update.') }
    finally { setEvaluating(false) }
  }

  function closeNavigation() { setMenuOpen(false); menuButton.current?.focus() }
  function navigate(next: Page) { setPage(next); if (menuOpen) closeNavigation() }
  useEffect(() => {
    if (!menuOpen) return
    function dismiss(event: KeyboardEvent) { if (event.key === 'Escape') closeNavigation() }
    document.addEventListener('keydown', dismiss)
    return () => document.removeEventListener('keydown', dismiss)
  }, [menuOpen])
  const records = overview?.records || []
  const recordMap = new Map(records.map(record => [record.record_id, record]))
  const decisions = new Map((result?.decisions || overview?.decisions || []).map(decision => [decision.record_id, decision]))
  const pending = result?.briefing.follow_ups.filter((_, index) => !reviews[index]).length || 0
  const selectedRecord = drawer?.kind === 'record' ? recordMap.get(drawer.id) : null
  const activeRecords = records.filter(record => ['open', 'blocked'].includes(record.status))
  const queue = [...activeRecords].filter(record => !['note', 'routine', 'contract', 'feature'].includes(record.category))
    .sort((a, b) => (decisions.get(b.record_id)?.urgency_score || 0) - (decisions.get(a.record_id)?.urgency_score || 0)
      || Number(['support', 'sales', 'cancellation'].includes(b.category)) - Number(['support', 'sales', 'cancellation'].includes(a.category))
      || (a.deadline || '9999').localeCompare(b.deadline || '9999')).slice(0, 4)
  const filtered = records.filter(record => (status === 'all' || record.status === status) && (category === 'all' || record.category === category)
    && `${record.record_id} ${record.title} ${record.description} ${record.customer_or_team}`.toLowerCase().includes(query.toLowerCase()))
  const eventList: Event[] = result?.events || job?.events || []

  return <div className="app-shell">
    <a className="skip-link" href="#main">Skip to workspace</a>
    {menuOpen && <button className="nav-backdrop" aria-label="Close navigation" onClick={closeNavigation} />}
    <aside className={`sidebar ${menuOpen ? 'is-open' : ''}`} id="navigation">
      <a href="#main" className="brand" aria-label="Praxis" onClick={() => navigate('overview')}><span className="brand-mark"><span /><span /><span /></span>Pra<span className="brand-accent">xis</span></a>
      <div className="workspace-switch"><span className="workspace-monogram">P</span><div><strong>Founder workspace</strong><small>Synthetic demonstration</small></div><ChevronRight size={15} /></div>
      <nav aria-label="Main navigation">{nav.map(({ id, label, icon: Icon }) => <button key={id} className={`nav-item ${page === id ? 'active' : ''}`} aria-current={page === id ? 'page' : undefined} onClick={() => navigate(id)}><Icon size={19} /><span>{label}</span>{id === 'followups' && pending > 0 && <span className="nav-count">{pending}</span>}</button>)}</nav>
      <div className="sidebar-note"><ShieldCheck size={21} /><strong>You stay in control.</strong><p>Review every recommendation. Approvals stay local; no messages are sent.</p></div>
      <div className="sidebar-bottom"><span className={`connection-dot ${overview ? 'connected' : ''}`} /><div><strong>{overview ? 'Workspace connected' : 'Connecting to workspace'}</strong><small>{overview ? `${records.length} synthetic business updates` : 'Waiting for the local API'}</small></div></div>
    </aside>

    <div className="workspace-main">
      <header className="topbar"><div className="breadcrumb"><button ref={menuButton} className="icon-button mobile-menu" aria-label="Open navigation" aria-expanded={menuOpen} aria-controls="navigation" onClick={() => menuOpen ? closeNavigation() : setMenuOpen(true)}><Menu size={21} /></button><span>Workspace</span><ChevronRight size={14} /><strong>{nav.find(item => item.id === page)?.label}</strong></div><div className="topbar-actions"><button className="search-link" onClick={() => navigate('updates')}><Search size={16} /><span>Search updates</span></button><span className="demo-indicator"><span />Demo data</span><span className="user-avatar" aria-label="Praxis workspace">P</span></div></header>
      <main id="main" className="main-content">
        {savedAt && <div className="saved-notice" role="status"><BookOpen size={18} /><div><strong>Viewing a saved real execution · {new Date(savedAt).toLocaleString()}</strong><p>No new agent or decision call was made. Activity and duration belong to the original run. Reviews start fresh for this viewing.</p></div></div>}
        {error && <div className="error-banner" role="alert"><CircleAlert size={19} /><div><strong>Something needs your attention</strong><p>{error}</p></div><button className="icon-button" aria-label="Dismiss error" onClick={() => setError('')}><X size={18} /></button></div>}
        {!overview ? <div className="connection-state"><div className="empty-icon">{error ? <Database size={28} /> : <LoaderCircle size={28} className="spin" />}</div><h1>{error ? 'Let’s reconnect your workspace.' : 'Opening your workspace…'}</h1><p>Your business records and metrics will appear once the local API responds.</p>{error && <button className="primary-button" onClick={() => setReload(reload + 1)}>Try again<ArrowRight size={17} /></button>}</div> : <>
          <div className="page-heading"><div><h1>{page === 'overview' ? 'Your morning, in focus.' : page === 'updates' ? 'The details behind your decisions.' : page === 'followups' ? 'Good follow-through starts here.' : page === 'decisions' ? 'A second perspective, with context.' : 'See the work behind the briefing.'}</h1><p>{page === 'overview' ? `${dateLabel(overview.reference_date, { weekday: 'long', year: 'numeric' })} · A clear view of what needs your attention.` : page === 'updates' ? 'Search the synthetic records that your agents use as evidence.' : page === 'followups' ? 'Inspect proposed messages and record your decision. Nothing is sent.' : page === 'decisions' ? 'Compare transparent rules with a bounded JEV decision. Keep uncertainty visible.' : 'Actual recorded tool completions, validation checks, and agent outcomes.'}</p></div><div className="heading-actions"><label className="sr-only" htmlFor="dataset">Dataset</label><select id="dataset" value={dataset} onChange={event => setDataset(event.target.value)} disabled={busy || submitting || evaluating}>{overview.datasets.map(item => <option value={item.id} key={item.id}>{item.name}</option>)}</select><button className="secondary-button export-button" disabled={!result} onClick={() => result && download(result)}><ArrowDownToLine size={16} />Export briefing</button></div></div>
          {overview.profile && <p className="dataset-context">{overview.profile.description}</p>}

          {page === 'overview' && <>
            <section className="metric-strip" aria-label="Calculated business metrics"><Metric label={overview.profile?.exposure_label || "Recorded contract exposure"} values={overview.metrics.exposure_by_currency} note={overview.profile?.exposure_note || "Linked to unresolved customer issues"} /><Metric label={overview.profile?.pipeline_label || "Potential sales pipeline"} values={overview.metrics.pipeline_by_currency} note={`${overview.metrics.opportunities_awaiting_action} ${overview.profile?.opportunities_label || "opportunities awaiting action"}`} /><div className="metric"><span>Open operational issues</span><strong>{overview.metrics.open_issues}<span className="metric-suffix">issues</span></strong><small>{overview.metrics.customer_escalations} {overview.profile?.escalations_label || "customer escalation records"}</small></div><div className="metric"><span>Overdue internal tasks</span><strong>{overview.metrics.overdue_tasks}<span className="metric-suffix">tasks</span></strong><small>Before the dataset reference date</small></div><button className="metric-info icon-button" aria-label="View metric definitions" onClick={() => setDrawer({ kind: 'metrics' })}><Info size={17} /></button></section>
            <section className="prompt-panel"><div className="prompt-heading"><span className="spark-icon"><Sparkles size={20} /></span><div><h2>What should we focus on?</h2><p>Your analyst gathers the evidence. Your Chief of Staff turns it into a plan.</p></div><Badge tone={overview.readiness.llm.configured ? 'success' : 'attention'}>{overview.readiness.llm.configured ? `${overview.readiness.llm.provider} configured` : 'API key needed'}</Badge></div><label className="sr-only" htmlFor="founder-question">Founder question</label><textarea id="founder-question" value={question} maxLength={2000} onChange={event => setQuestion(event.target.value)} disabled={busy || submitting || evaluating} placeholder="Ask about priorities, renewal risk, or a blocked release…" /><div className="prompt-footer"><div className="example-prompts"><button onClick={() => setQuestion(MORNING)} disabled={busy || submitting || evaluating}>Morning priorities<ArrowUpRight size={13} /></button><button onClick={() => setQuestion(overview.profile?.comparison_question || EXPLAIN)} disabled={busy || submitting || evaluating}>{overview.profile?.comparison_label || "Renewal vs. feature"}<ArrowUpRight size={13} /></button></div><div className="run-controls"><label className="sr-only" htmlFor="decision-provider">Decision provider</label><select id="decision-provider" value={decisionProvider} disabled={busy || submitting || evaluating} onChange={event => setDecisionProvider(event.target.value)}><option value="rules">Rules signals</option><option value="jev">JEV · one update</option></select><button className="primary-button" onClick={generate} disabled={busy || submitting || evaluating || !question.trim() || !overview.readiness.llm.configured || (decisionProvider === 'jev' && !overview.readiness.jev.configured)}>{busy ? <><LoaderCircle size={17} className="spin" />Preparing · {elapsedLabel(elapsed)}</> : <>Prepare my briefing<ArrowRight size={17} /></>}</button></div></div>{decisionProvider === 'jev' && <p className="provider-note">JEV covers {decisionRecord} only; other updates use labeled rules signals. Saved live decisions are reused. {overview.readiness.jev.configured ? 'At most one new JEV decision per run.' : 'Add JEV_API_KEY privately to .env and restart the API.'}</p>}</section>

            <SavedBriefings key={dataset} dataset={dataset} disabled={Boolean(busy || submitting || evaluating)} onOpen={openSaved} />
            {busy && <section className="working-state" role="status"><LoaderCircle className="spin" size={23} /><div><strong>Your briefing is in progress.</strong><p>The server is processing real business evidence. Provider limits may add a wait; recorded activity appears when the run finishes.</p></div><span>{elapsedLabel(elapsed)}</span></section>}
            {result ? <><section className="summary-panel"><div className="section-heading"><div className="section-title"><CheckCheck size={19} /><h2>Your founder briefing</h2></div><Badge tone="success">{savedAt ? 'Saved real run' : 'Live run complete'}</Badge></div><p className="summary-text">{result.briefing.executive_summary}</p><div className="summary-meta"><span>{result.model}</span><span>{result.elapsed_seconds.toFixed(1)}s {savedAt ? 'original execution' : 'elapsed'}</span><span>Sources & structure checked</span></div><details className="answered-question"><summary>Question answered</summary><p>{result.question}</p></details></section><div className="content-grid"><section><div className="section-heading"><h2>Your top priorities</h2><span className="muted">Model judgments · review the evidence</span></div><div className="priority-list">{result.briefing.priorities.map(priority => <PriorityCard key={priority.record_id} priority={priority} onEvidence={id => setDrawer({ kind: 'record', id })} />)}</div></section><aside className="right-column"><DeadlinePanel overview={overview} records={recordMap} onEvidence={id => setDrawer({ kind: 'record', id })} /><div className="next-step-panel"><MessageSquareText size={22} /><h3>Turn clarity into follow-through.</h3><p>{result.briefing.follow_ups.length} proposed follow-up{result.briefing.follow_ups.length === 1 ? '' : 's'} ready for your review.</p><button className="text-button" onClick={() => navigate('followups')}>Review the drafts<ArrowRight size={16} /></button></div><section className="limitations-panel"><h3>What still needs context</h3>{result.briefing.data_limitations.length ? result.briefing.data_limitations.map((limitation, index) => <p key={index}><Info size={15} />{limitation}</p>) : <p>Source checking does not prove every model interpretation. Confirm important conclusions before acting.</p>}</section></aside></div></> : <div className="content-grid"><section><div className="section-heading"><h2>Your attention queue</h2><Badge>Rules overview</Badge></div><p className="section-description">A first look at active updates. Run a briefing for the agents’ ranked recommendations.</p><div className="queue-list">{queue.map(record => <button className="queue-item" key={record.record_id} onClick={() => setDrawer({ kind: 'record', id: record.record_id })}><span className={`queue-symbol ${urgencyTone(decisions.get(record.record_id)?.urgency || '')}`}>{record.category === 'support' ? <CircleAlert size={20} /> : record.category === 'sales' ? <ArrowUpRight size={20} /> : <FileText size={20} />}</span><span className="queue-copy"><span className="queue-topline"><Badge tone={urgencyTone(decisions.get(record.record_id)?.urgency || '')}>{decisions.get(record.record_id)?.urgency || 'Needs attention'}</Badge><small>{record.customer_or_team}</small></span><strong>{record.title}</strong><span>{record.description}</span><small>{record.record_id}<span className="separator">·</span>{dueLabel(record.deadline, overview.reference_date)}</small></span><ChevronRight size={18} /></button>)}</div></section><aside className="right-column"><DeadlinePanel overview={overview} records={recordMap} onEvidence={id => setDrawer({ kind: 'record', id })} /><section className="source-panel"><div className="section-heading"><h3>Grounded in your updates</h3><Database size={17} /></div>{Object.entries(records.reduce<Record<string, number>>((counts, record) => ({ ...counts, [record.source]: (counts[record.source] || 0) + 1 }), {})).slice(0, 5).map(([source, count]) => <div className="source-row" key={source}><span className="source-icon"><FileText size={15} /></span><span>{source.replace(/^Synthetic /, '')}</span><strong>{count}</strong></div>)}<p className="fine-print">Synthetic source records. No external accounts are connected.</p></section></aside></div>}
          </>}

          {page === 'updates' && <section className="records-panel"><div className="table-toolbar"><label className="search-field"><Search size={17} /><input value={query} onChange={event => setQuery(event.target.value)} placeholder="Search customer, issue, or record ID" aria-label="Search business updates" /></label><select aria-label="Filter status" value={status} onChange={event => setStatus(event.target.value)}><option value="all">All statuses</option>{['open', 'blocked', 'completed', 'cancelled'].map(value => <option key={value}>{value}</option>)}</select><select aria-label="Filter category" value={category} onChange={event => setCategory(event.target.value)}><option value="all">All categories</option>{[...new Set(records.map(record => record.category))].map(value => <option key={value}>{value}</option>)}</select></div><div className="table-wrap"><table><thead><tr><th>Update</th><th>Owner</th><th>Status</th><th>Deadline</th><th>Recorded value</th><th><span className="sr-only">Evidence</span></th></tr></thead><tbody>{filtered.map(record => <tr key={record.record_id}><td><button className="record-title" onClick={() => setDrawer({ kind: 'record', id: record.record_id })}>{record.title}<small>{record.record_id} · {record.customer_or_team}</small></button></td><td>{record.owner || 'Unassigned'}</td><td><Badge tone={record.status === 'blocked' ? 'attention' : record.status === 'completed' ? 'success' : 'neutral'}>{record.status}</Badge></td><td>{record.deadline ? dateLabel(record.deadline) : 'Not recorded'}</td><td className="money-cell">{record.contract_value !== null ? money(record.contract_value, record.currency || 'USD') : <span className="muted">Not recorded</span>}</td><td><button className="icon-button" aria-label={`Inspect ${record.record_id}`} onClick={() => setDrawer({ kind: 'record', id: record.record_id })}><ArrowUpRight size={17} /></button></td></tr>)}</tbody></table></div>{!filtered.length && <EmptyState icon={<Search />} title="No matching updates" description="Try another search or clear the filters to see more records." />}<footer className="table-footer">{filtered.length} of {records.length} updates · {overview.label.toLowerCase()}</footer></section>}

          {page === 'followups' && <>{!result || !result.briefing.follow_ups.length ? <EmptyState icon={<MessageSquareText />} title="Your follow-up queue starts with a briefing." description="Run the agents from Overview to create grounded drafts for your review." action={<button className="primary-button" onClick={() => navigate('overview')}>Prepare a briefing<ArrowRight size={16} /></button>} /> : <><div className="review-notice"><ShieldCheck size={19} /><span>Approvals are local to this browser session. There is no send action or external account connection.</span></div><div className="followup-list">{result.briefing.follow_ups.map((draft, index) => <article className={`followup-card ${reviews[index] || ''}`} key={`${result.run_id}:${index}`}><header><span className="team-avatar">{initials(draft.recipient_team)}</span><div><h2>Follow up with {draft.recipient_team}</h2><button className="source-link" onClick={() => setDrawer({ kind: 'record', id: draft.record_id })}>{draft.record_id}<ArrowUpRight size={13} /></button></div><Badge tone={reviews[index] === 'approved' ? 'success' : reviews[index] === 'rejected' ? 'neutral' : 'attention'}>{reviews[index] ? `${reviews[index]} locally` : 'Awaiting your review'}</Badge></header><div className="draft-body">{draft.draft}</div><footer><button className="secondary-button" onClick={async () => { try { await navigator.clipboard.writeText(draft.draft); setCopied(index) } catch { setError('Your browser could not copy the draft. Select the text and copy it manually.') } }}><Copy size={15} />{copied === index ? 'Copied' : 'Copy draft'}</button><div><button className="secondary-button" onClick={() => setReviews({ ...reviews, [index]: 'rejected' })}><X size={15} />Reject</button><button className="primary-button approve-button" onClick={() => setReviews({ ...reviews, [index]: 'approved' })}><Check size={16} />Approve locally</button></div></footer></article>)}</div></>}</>}

          {page === 'decisions' && <div className="decision-layout"><section className="decision-intro"><span className="decision-icon"><FlaskConical size={27} /></span><h2>A decision signal.<br />You make the call.</h2><p>JEV evaluates a bounded question about one update: which team should own it, how urgent it appears, and whether a customer relationship may be at risk.</p><div className="decision-budget"><ShieldCheck size={18} /><div><strong>Built for a limited allowance</strong><p>Three questions share one request. A genuine saved result is reused for repeat views; no bulk evaluation runs automatically.</p></div></div><Badge tone={overview.readiness.jev.configured ? 'success' : 'attention'}>{overview.readiness.jev.configured ? 'JEV key configured' : 'JEV key required'}</Badge><p className="fine-print">Model: {overview.readiness.jev.model}. Rules scores are heuristics; JEV probabilities are model estimates. Mandatory policies always take precedence.</p></section><section className="decision-panel"><label className="field-label" htmlFor="decision-record">Choose an update</label><select id="decision-record" value={decisionRecord} onChange={event => { setDecisionRecord(event.target.value); setComparison(null) }} disabled={evaluating || busy || submitting}>{records.filter(record => ['open', 'blocked'].includes(record.status)).map(record => <option key={record.record_id} value={record.record_id}>{record.record_id} · {record.title}</option>)}</select><div className="selected-decision-record"><Badge>{recordMap.get(decisionRecord)?.category}</Badge><h3>{recordMap.get(decisionRecord)?.title}</h3><p>{recordMap.get(decisionRecord)?.description}</p><button className="text-button" onClick={() => setDrawer({ kind: 'record', id: decisionRecord })}>Inspect source evidence<ArrowUpRight size={15} /></button></div><button className="primary-button decision-run" onClick={evaluate} disabled={evaluating || busy || submitting || !overview.readiness.jev.configured}>{evaluating ? <><LoaderCircle className="spin" size={17} />Evaluating…</> : <><FlaskConical size={17} />{overview.readiness.jev.cached_record_id === decisionRecord ? 'View saved live decision' : 'Evaluate with JEV · uses one request'}</>}</button>{!overview.readiness.jev.configured && <p className="provider-note">Add JEV_API_KEY to the server’s .env and restart the backend. No key belongs in this browser.</p>}{comparison && <div className="comparison-result"><div className="section-heading"><h3>Decision result</h3><Badge tone="success">{comparison.cached ? 'Saved live decision' : 'Live JEV result'}</Badge></div><div className="comparison-columns"><div><span>Rules baseline</span><strong>{comparison.baseline.classification}</strong><Badge tone={urgencyTone(comparison.baseline.urgency)}>{comparison.baseline.urgency}</Badge><p>{comparison.baseline.urgency_score} / 3 · heuristic</p></div><div><span>JEV signal</span><strong>{comparison.jev.classification}</strong><Badge tone={urgencyTone(comparison.jev.urgency)}>{comparison.jev.urgency}</Badge><p>{comparison.jev.urgency_score} / 3 · expected score</p></div></div>{comparison.jev.risk_probability !== null && <div className="risk-estimate"><span>Customer relationship risk</span><strong>{(comparison.jev.risk_probability * 100).toFixed(1)}%</strong><small>Model probability estimate; not a confirmed outcome</small></div>}{comparison.jev.probabilities && <div className="distribution"><h4>Responsible team distribution</h4>{Object.entries(comparison.jev.probabilities).map(([team, value]) => <div key={team}><span>{team}</span><meter min={0} max={1} value={value} aria-label={`${team} probability`} /><strong>{(value * 100).toFixed(1)}%</strong></div>)}</div>}<p className="fine-print">{comparison.jev.uncertainty}</p><div className="decision-provenance"><span>{comparison.jev.model_version || comparison.jev.provider}</span>{comparison.jev.evaluated_at && <span>Evaluated {new Date(comparison.jev.evaluated_at).toLocaleString()}</span>}<span>{comparison.cached ? 'No new API call for this view' : 'One live decision requested'}</span></div></div>}</section></div>}

          {page === 'activity' && <>{!eventList.length ? <EmptyState icon={<Activity />} title={busy ? 'A live run is in progress.' : 'Your execution trail will appear here.'} description="Completed tools and task outcomes are recorded by the server. We never fill this view with simulated agent steps." action={!busy && <button className="primary-button" onClick={() => navigate('overview')}>Open your workspace<ArrowRight size={16} /></button>} /> : <section className="activity-panel"><div className="section-heading"><h2>Recorded execution</h2><span className="muted">{eventList.length} actual events</span></div><ol className="event-list">{eventList.map((event, index) => <li key={`${event.timestamp}:${index}`}><span className={`event-symbol ${event.kind === 'error' ? 'event-error' : ''}`}>{event.kind === 'tool' ? <Database size={16} /> : event.kind === 'task' ? <CheckCheck size={16} /> : <ShieldCheck size={16} />}</span><div><div className="event-heading"><strong>{event.tool || event.actor}</strong><time dateTime={event.timestamp}>{new Date(event.timestamp).toLocaleTimeString()}</time></div><p>{event.detail}</p><small>{event.actor} · {event.kind}</small>{event.source_ids.length > 0 && <div className="event-sources">{event.source_ids.slice(0, 8).map(id => <button key={id} onClick={() => setDrawer({ kind: 'record', id })}>{id}</button>)}{event.source_ids.length > 8 && <span>+{event.source_ids.length - 8} records</span>}</div>}</div></li>)}</ol></section>}</>}
          <footer className="workspace-footer"><span><ShieldCheck size={14} />SYNTHETIC DEMONSTRATION DATA</span><span>Reference date {dateLabel(overview.reference_date, { year: 'numeric' })} · Human approval always required</span></footer>
        </>}
      </main>
    </div>

    <dialog className="evidence-drawer" ref={dialog} onClose={() => setDrawer(null)} onClick={event => { if (event.target === event.currentTarget) setDrawer(null) }} aria-labelledby="drawer-title"><div className="drawer-inner"><header className="drawer-header"><span><BookOpen size={19} />{drawer?.kind === 'metrics' ? 'Metric definitions' : 'Source evidence'}</span><button className="icon-button" aria-label="Close evidence" onClick={() => setDrawer(null)}><X size={20} /></button></header>{drawer?.kind === 'metrics' && overview ? <><h2 id="drawer-title">Know what the numbers mean.</h2><p className="drawer-lead">Calculated from the dataset, with distinct contract and opportunity cohorts.</p>{Object.entries(overview.metrics.definitions).map(([name, description]) => <section className="definition" key={name}><h3>{name.replaceAll('_', ' ')}</h3><p>{description}</p>{overview.metrics.cohorts[name] && <div className="source-chips">{overview.metrics.cohorts[name].map(id => <button key={id} onClick={() => setDrawer({ kind: 'record', id })}>{id}<ArrowUpRight size={12} /></button>)}</div>}</section>)}</> : selectedRecord ? <><Badge tone={selectedRecord.severity === 'critical' ? 'critical' : 'neutral'}>{selectedRecord.record_id} · {selectedRecord.status}</Badge><h2 id="drawer-title">{selectedRecord.title}</h2><p className="drawer-lead">Observed source record · {selectedRecord.source}</p><dl className="record-facts"><div><dt>Customer / team</dt><dd>{selectedRecord.customer_or_team}</dd></div><div><dt>Recorded owner</dt><dd>{selectedRecord.owner || 'Unassigned'}</dd></div><div><dt>Deadline</dt><dd>{selectedRecord.deadline ? dateLabel(selectedRecord.deadline, { year: 'numeric' }) : 'Not recorded'}</dd></div><div><dt>Recorded value</dt><dd>{selectedRecord.contract_value !== null ? money(selectedRecord.contract_value, selectedRecord.currency || 'USD') : 'Not recorded'}</dd></div><div><dt>Category</dt><dd>{selectedRecord.category}</dd></div><div><dt>Created</dt><dd>{dateLabel(selectedRecord.created_at, { year: 'numeric' })}</dd></div></dl><section className="source-description"><h3>What the update says</h3><p>{selectedRecord.description}</p></section><section className="linked-evidence"><h3>Related evidence</h3>{selectedRecord.related_record_ids.length ? selectedRecord.related_record_ids.map(id => <button key={id} onClick={() => setDrawer({ kind: 'record', id })}><span><small>{id}</small><strong>{recordMap.get(id)?.title || 'Record unavailable'}</strong></span><ArrowUpRight size={16} /></button>) : <p className="muted">No related records are linked to this update.</p>}</section><p className="evidence-footnote"><ShieldCheck size={16} />All records are synthetic. Recommendations elsewhere are model judgments, not additional source facts.</p></> : <h2 id="drawer-title">Source record unavailable</h2>}</div></dialog>
  </div>
}

function Metric({ label, values, note }: { label: string; values: Record<string, string>; note: string }) {
  return <div className="metric"><span>{label}</span><strong className="financial-value">{Object.entries(values).length ? Object.entries(values).map(([currency, value]) => <span key={currency}>{money(value, currency)}<small>{currency}</small></span>) : 'Not recorded'}</strong><small>{note}</small></div>
}
function PriorityCard({ priority, onEvidence }: { priority: Priority; onEvidence: (id: string) => void }) {
  return <article className="priority-card"><header><span className="priority-rank">{priority.rank.toString().padStart(2, '0')}</span><div><Badge tone={urgencyTone(priority.urgency)}>{priority.urgency}</Badge><h3>{priority.title}</h3></div></header><p className="impact-text">{priority.business_impact}</p><div className="recommended-action"><span>Recommended next step</span><p>{priority.recommended_action}</p></div><footer><span className="owner"><span className="team-avatar small">{initials(priority.suggested_owner)}</span>{priority.suggested_owner}</span><div className="source-chips">{priority.source_ids.map(id => <button key={id} onClick={() => onEvidence(id)}>{id}<ArrowUpRight size={12} /></button>)}</div></footer>{priority.assumptions.length > 0 && <details className="assumptions"><summary>Assumptions & missing context</summary>{priority.assumptions.map((text, index) => <p key={index}>{text}</p>)}</details>}</article>
}
function DeadlinePanel({ overview, records, onEvidence }: { overview: Overview; records: Map<string, BusinessRecord>; onEvidence: (id: string) => void }) {
  const risks = [...overview.deadlines.risks].sort((a, b) => Number(a.overdue) - Number(b.overdue) || a.days_remaining - b.days_remaining).slice(0, 4)
  return <section className="deadline-panel"><div className="section-heading"><h3>Coming up soon</h3><Clock3 size={17} /></div><div className="deadline-list">{risks.map(risk => <button key={risk.record_id} onClick={() => onEvidence(risk.record_id)}><span className="calendar-date"><small>{dateLabel(risk.deadline, { month: 'short', day: undefined })}</small><strong>{new Date(`${risk.deadline}T12:00:00Z`).getUTCDate()}</strong></span><span><strong>{records.get(risk.record_id)?.title}</strong><small className={risk.days_remaining <= 1 ? 'deadline-urgent' : ''}>{dueLabel(risk.deadline, overview.reference_date)}</small></span><ChevronRight size={15} /></button>)}</div><p className="fine-print">{overview.metrics.overdue_tasks} internal tasks are also overdue. Dates use the fixed demo reference.</p></section>
}
function EmptyState({ icon, title, description, action }: { icon: ReactNode; title: string; description: string; action?: ReactNode }) {
  return <section className="empty-state"><span className="empty-icon">{icon}</span><h2>{title}</h2><p>{description}</p>{action}</section>
}
