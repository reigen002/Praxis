import { useState } from 'react'
import { ArrowRight, BookOpen, LoaderCircle } from 'lucide-react'
import { api } from './api'
import type { RunResult } from './types'

export type SavedRun = { saved_at: string; result: RunResult }

export default function SavedBriefings({ dataset, disabled, onOpen }: {
  dataset: string; disabled: boolean; onOpen: (saved: SavedRun) => void
}) {
  const [expanded, setExpanded] = useState(false)
  const [loading, setLoading] = useState(false)
  const [runs, setRuns] = useState<SavedRun[]>([])
  const [message, setMessage] = useState('')
  async function toggle() {
    if (expanded) { setExpanded(false); return }
    setExpanded(true); setLoading(true); setMessage(''); setRuns([])
    try {
      const response = await api<{ runs: SavedRun[]; warnings: string[] }>(`/saved-runs?dataset=${encodeURIComponent(dataset)}`)
      setRuns(response.runs); setMessage(response.warnings.join(' '))
    } catch { setMessage('Saved briefings could not be loaded. Close and reopen this panel to retry.') }
    finally { setLoading(false) }
  }
  return <section className="saved-briefings" aria-label="Saved briefings">
    <div className="saved-heading"><button className="text-button" disabled={disabled || loading}
      aria-expanded={expanded} aria-controls="saved-runs-list" onClick={toggle}>
      {loading ? <LoaderCircle size={17} className="spin" /> : <BookOpen size={17} />}
      {expanded ? 'Close saved briefings' : 'Open saved briefings'}
    </button><span>Revisit a real execution · no new API usage</span></div>
    {expanded && <div id="saved-runs-list">
      {loading && <p role="status">Checking saved evidence…</p>}
      {message && <p role="status">{message}</p>}
      {!loading && !message && !runs.length && <p>No verified saved run matches this dataset yet. Complete a live briefing to save one.</p>}
      {runs.map(saved => {
        const title = saved.result.question.startsWith('Why ') ? 'Open decision explanation'
          : saved.result.question.startsWith('Prepare my founder briefing') ? 'Open morning briefing' : 'Open saved briefing'
        const executed = saved.result.events.at(-1)?.timestamp || saved.saved_at
        return <article className="saved-run" key={saved.result.run_id}>
          <div><p>{saved.result.question}</p><small>{new Date(executed).toLocaleString()} · {saved.result.model} · {saved.result.elapsed_seconds.toFixed(1)}s original execution</small></div>
          <button className="secondary-button" disabled={disabled} onClick={() => onOpen(saved)}>{title}<ArrowRight size={15} /></button>
        </article>
      })}
    </div>}
  </section>
}
