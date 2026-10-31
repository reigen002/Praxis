import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import type { BusinessRecord, Overview, RunResult } from './types'
import dataset from '../../data/synthetic/founder_demo.json'
import schoolDataset from '../../data/synthetic/yfs_operations.json'
import { money } from './format'

function overview(): Overview {
  return { dataset: 'demo', label: dataset.label, reference_date: dataset.reference_date,
    datasets: [{ id: 'demo', name: 'Founder demo' }, { id: 'original', name: 'Original' }],
    records: dataset.records as BusinessRecord[], metrics: { exposure_by_currency: { USD: '84000.25' },
      pipeline_by_currency: { USD: '172000' }, open_issues: 11, overdue_tasks: 3, customer_escalations: 4,
      opportunities_awaiting_action: 3, missing_financial_ids: ['CAN-002'], definitions: { exposure: 'Recorded contract face value.' },
      cohorts: { exposure: ['CON-001', 'CON-002'] }, source_ids: [] },
    deadlines: { risks: [{ record_id: 'INC-001', deadline: '2026-10-30', days_remaining: 1, overdue: false }] },
    policy: { escalations: [{ record_id: 'INC-001', reason: 'Critical service/renewal policy', source_ids: ['INC-001', 'CON-001'] }] },
    decisions: [{ record_id: 'INC-001', classification: 'Engineering', urgency: 'Critical', urgency_score: 3,
      provider: 'rules-v1', probabilities: null, risk_probability: null, uncertainty: 'Heuristic', error: null, fallback: false }],
    readiness: { llm: { configured: true, provider: 'groq', model: 'openai/gpt-oss-120b' },
      jev: { configured: true, model: 'jev-1.13', live_verified: false, cached_record_id: null, max_records_per_run: 1 } } }
}
function run(): RunResult {
  return { run_id: 'test-run', question: 'Test fixture only', model: 'scripted-test-fixture', mode: 'live', elapsed_seconds: 1,
    briefing: { executive_summary: 'Customer recovery needs founder attention.', priorities: [{ rank: 1, record_id: 'INC-001', title: 'Restore the integration', category: 'support', urgency: 'Critical', business_impact: 'The renewal may be at risk.', recommended_action: 'Confirm recovery with Engineering.', suggested_owner: 'Engineering', source_ids: ['INC-001', 'CON-001'], assumptions: [] }], follow_ups: [{ record_id: 'INC-001', recipient_team: 'Customer Success', draft: 'Please confirm restoration and share the recovery plan.', source_ids: ['INC-001'], approval_required: true }], data_limitations: [] },
    metrics: overview().metrics, decisions: overview().decisions, events: [] }
}
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
beforeEach(() => vi.stubGlobal('fetch', vi.fn().mockImplementation(() => Promise.resolve(json(overview())))))
afterEach(() => { vi.unstubAllGlobals(); vi.useRealTimers() })

describe('Founder workspace', () => {
  it('opens a saved genuine run without POST and labels its historical execution', async () => {
    const saved = { saved_at: '2026-10-31T06:00:00Z', result: { ...run(),
      question: 'Prepare my founder briefing for today. What are the three most important issues, and why?' } }
    vi.mocked(fetch).mockImplementation(url => Promise.resolve(json(String(url).includes('/saved-runs')
      ? { runs: [saved], warnings: [] } : overview())))
    render(<App />)
    await screen.findByText('$84,000.25')
    fireEvent.click(screen.getByRole('button', { name: 'Open saved briefings' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Open morning briefing' }))
    expect(await screen.findByText('Customer recovery needs founder attention.')).toBeInTheDocument()
    expect(screen.getByText('Saved real run')).toBeInTheDocument()
    expect(screen.queryByText('Live run complete')).not.toBeInTheDocument()
    expect(screen.getByText(/No new agent or decision call/)).toBeInTheDocument()
    expect(vi.mocked(fetch).mock.calls.every(([, options]) => !options?.method || options.method === 'GET')).toBe(true)
    fireEvent.click(screen.getByRole('button', { name: /Follow-up review/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Approve locally' }))
    expect(screen.getByText(/approved locally/)).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Dataset'), { target: { value: 'original' } })
    await waitFor(() => expect(screen.queryByText(/Viewing a saved real execution/)).not.toBeInTheDocument())
    expect(screen.queryByText('Saved real run')).not.toBeInTheDocument()
    expect(screen.queryByText(/approved locally/)).not.toBeInTheDocument()
  })

  it('opens the research-informed school demo with programme labels and its comparison prompt', async () => {
    const school: Overview = { ...overview(), dataset: 'yfs', reference_date: schoolDataset.reference_date,
      datasets: [{ id: 'yfs', name: 'YFS founder demo' }, { id: 'demo', name: 'Startup demo · saved JEV' }],
      records: schoolDataset.records as BusinessRecord[], profile: {
        description: 'Fictional programme operations, not internal school data.',
        comparison_question: 'Why is the cohort access issue more urgent than the certificate preview redesign?',
        comparison_label: 'Cohort vs. redesign', exposure_label: 'Programme agreement exposure',
        exposure_note: 'Signed programme agreements', pipeline_label: 'Potential partnership pipeline',
        opportunities_label: 'programme proposals awaiting action', escalations_label: 'school or sponsor issue records' },
      metrics: { ...overview().metrics, exposure_by_currency: { INR: '300000' }, pipeline_by_currency: { INR: '340000' } } }
    vi.mocked(fetch).mockResolvedValue(json(school))
    render(<App />)
    expect(await screen.findByText('Programme agreement exposure')).toBeInTheDocument()
    expect(screen.getByText('Potential partnership pipeline')).toBeInTheDocument()
    expect(screen.getByText('Fictional programme operations, not internal school data.')).toBeInTheDocument()
    expect(screen.getByLabelText('Dataset')).toHaveValue('yfs')
    expect(fetch).toHaveBeenCalledWith('/api/overview?dataset=yfs', expect.anything())
    fireEvent.click(screen.getByRole('button', { name: 'Cohort vs. redesign' }))
    expect(screen.getByLabelText('Founder question')).toHaveValue(school.profile!.comparison_question)
  })

  it('renders actual metrics without discarding cents and opens source evidence', async () => {
    render(<App />)
    expect(await screen.findByText('$84,000.25')).toBeInTheDocument()
    const record = dataset.records.find(record => record.record_id === 'INC-001')!
    fireEvent.click(screen.getAllByText(record.title)[0])
    const dialog = screen.getByRole('dialog')
    expect(within(dialog).getByRole('heading', { name: record.title })).toBeInTheDocument()
    expect(within(dialog).getByText(record.description)).toBeInTheDocument()
    fireEvent.click(within(dialog).getByRole('button', { name: 'Close evidence' }))
    expect(dialog).not.toHaveAttribute('open')
  })

  it('blocks dataset changes while a submission or JEV request is pending', async () => {
    let resolveSubmission!: (response: Response) => void
    vi.mocked(fetch).mockImplementation(url => String(url).includes('/runs') ? new Promise(resolve => { resolveSubmission = resolve }) : Promise.resolve(json(overview())))
    render(<App />)
    await screen.findByText('$84,000.25')
    fireEvent.click(screen.getByRole('button', { name: 'Prepare my briefing' }))
    expect(screen.getByLabelText('Dataset')).toBeDisabled()
    expect(screen.getByRole('button', { name: /Prepare my briefing|Starting/ })).toBeDisabled()
    await act(async () => resolveSubmission(json({ id: 'test', status: 'completed', result: run(), error: null, events: [] })))
    expect(await screen.findByText('Customer recovery needs founder attention.')).toBeInTheDocument()
  })

  it('keeps a job after a transient poll failure and later renders the completed run', async () => {
    let polls = 0
    vi.mocked(fetch).mockImplementation(url => {
      const path = String(url)
      if (path === '/api/runs') return Promise.resolve(json({ id: 'test', status: 'queued', result: null, error: null, events: [] }))
      if (path === '/api/runs/test') return ++polls === 1 ? Promise.reject(new TypeError('Connection lost')) : Promise.resolve(json({ id: 'test', status: 'completed', result: run(), error: null, events: [] }))
      return Promise.resolve(json(overview()))
    })
    render(<App />)
    await screen.findByText('$84,000.25')
    vi.useFakeTimers()
    await act(async () => fireEvent.click(screen.getByRole('button', { name: 'Prepare my briefing' })))
    await act(async () => vi.advanceTimersByTimeAsync(2000))
    expect(screen.getByText(/Keeping the run ID/)).toBeInTheDocument()
    expect(screen.getByLabelText('Dataset')).toBeDisabled()
    await act(async () => vi.advanceTimersByTimeAsync(2000))
    expect(screen.getByText('Customer recovery needs founder attention.')).toBeInTheDocument()
    expect(screen.queryByText(/Keeping the run ID/)).not.toBeInTheDocument()
  })

  it('records local approval without sending another request', async () => {
    vi.mocked(fetch).mockImplementation(url => Promise.resolve(json(String(url) === '/api/runs'
      ? { id: 'test', status: 'completed', result: run(), error: null, events: [] } : overview())))
    render(<App />)
    await screen.findByText('$84,000.25')
    fireEvent.click(screen.getByRole('button', { name: 'Prepare my briefing' }))
    await screen.findByText('Customer recovery needs founder attention.')
    fireEvent.click(screen.getByRole('button', { name: /Follow-up review/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Approve locally' }))
    expect(screen.getByText('approved locally')).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledTimes(2)
    fireEvent.click(screen.getByRole('button', { name: 'Reject' }))
    expect(screen.getByText('rejected locally')).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledTimes(2)
  })

  it('offers a clear recovery state when the backend is unavailable', async () => {
    vi.mocked(fetch).mockRejectedValue(new TypeError('Offline'))
    render(<App />)
    expect(await screen.findByText('Let’s reconnect your workspace.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Try again' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Prepare my briefing' })).not.toBeInTheDocument()
  })

  it('evaluates JEV only on request and preserves fractional scores and saved provenance', async () => {
    const baseline = overview().decisions[0]
    vi.mocked(fetch).mockImplementation(url => Promise.resolve(json(String(url) === '/api/decisions/evaluate'
      ? { baseline, cached: true, jev: { ...baseline, provider: 'jev-ai.org', urgency_score: 2.81,
          risk_probability: 0.87, cache_hit: true, uncertainty: 'Mocked JEV response for UI testing only.',
          model_version: 'jev-1.13-test', probabilities: { Engineering: 0.8, 'Customer Success': 0.2 } } }
      : overview())))
    render(<App />)
    await screen.findByText('$84,000.25')
    fireEvent.click(screen.getByRole('button', { name: 'Decision lab' }))
    expect(fetch).toHaveBeenCalledTimes(1)
    fireEvent.click(screen.getByRole('button', { name: /Evaluate with JEV/ }))
    expect(await screen.findByText('2.81 / 3 · expected score')).toBeInTheDocument()
    expect(screen.getByText('87.0%')).toBeInTheDocument()
    expect(screen.getByText('Saved live decision')).toBeInTheDocument()
    expect(screen.getByText('No new API call for this view')).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledTimes(2)
  })

  it('dismisses navigation with Escape and restores focus to its toggle', async () => {
    render(<App />)
    await screen.findByText('$84,000.25')
    const toggle = screen.getByRole('button', { name: 'Open navigation' })
    fireEvent.click(toggle)
    expect(toggle).toHaveAttribute('aria-expanded', 'true')
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
    expect(toggle).toHaveFocus()
  })
})

it('formats monetary cents exactly for the demo range', () => {
  expect(money('84000.25', 'USD')).toBe('$84,000.25')
})
