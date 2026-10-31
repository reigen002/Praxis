/** Real-browser rehearsal using installed Chrome and Node's built-in CDP client.
 * Run outside the coding sandbox. Makes one Rules/Groq UI run; blocks JEV routes.
 */
import { spawn } from 'node:child_process'
import { existsSync } from 'node:fs'
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const savedMode = process.argv.includes('--saved')
const output = join(root, 'artifacts', savedMode ? 'rehearsal-praxis-saved' : 'rehearsal-praxis-live')
const base = 'http://127.0.0.1:8000'
const chromePath = ['C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe'].find(existsSync)
const report = { started_at: new Date().toISOString(), mode: savedMode ? 'real browser, saved genuine executions; no new inference' : 'real browser, Rules/Groq', dataset: 'yfs',
  checks: [], screenshots: [], posts: [], console_errors: [], jev_requests_blocked: 0, cached_jev_reads: 0 }
const delay = ms => new Promise(resolve => setTimeout(resolve, ms))
let browser, socket, serial = 0
const pending = new Map()

async function localJson(path, timeout) {
  let response
  try {
    response = await fetch(base + path, { signal: AbortSignal.timeout(timeout) })
  } catch {
    throw new Error(`Cannot reach Praxis at ${base}${path}. Start the backend on port 8000 and leave its terminal open, then rerun this helper.`)
  }
  if (!response.ok) throw new Error(`Praxis returned HTTP ${response.status} for ${path}. Check the backend terminal.`)
  return response.json()
}

function check(name, passed, details = null) {
  report.checks.push({ name, passed: !!passed, details })
  if (!passed) throw new Error(name)
  console.log('PASS:', name)
}
async function until(callback, timeout = 20000) {
  const end = Date.now() + timeout
  while (Date.now() < end) {
    const value = await callback()
    if (value) return value
    await delay(250)
  }
  throw new Error('Timed out waiting for the browser/application')
}
function rpc(method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = ++serial
    const timer = setTimeout(() => { pending.delete(id); reject(new Error(`CDP timeout: ${method}`)) }, 15000)
    pending.set(id, { resolve, reject, timer })
    socket.send(JSON.stringify({ id, method, params }))
  })
}
async function evaluate(expression) {
  const response = await rpc('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true })
  if (response.exceptionDetails) throw new Error(response.exceptionDetails.text)
  return response.result.value
}
async function click(expression) {
  const point = await evaluate(`(() => { const e = ${expression};
    if (!e || e.disabled) return null; e.scrollIntoView({block:'center'});
    const r = e.getBoundingClientRect(); return {x:r.x+r.width/2,y:r.y+r.height/2}; })()`)
  if (!point) throw new Error(`Control unavailable: ${expression}`)
  await rpc('Input.dispatchMouseEvent', { type: 'mousePressed', ...point, button: 'left', clickCount: 1 })
  await rpc('Input.dispatchMouseEvent', { type: 'mouseReleased', ...point, button: 'left', clickCount: 1 })
}
const button = text => `[...document.querySelectorAll('button')].find(e => e.textContent.trim() === ${JSON.stringify(text)})`
const nav = text => `[...document.querySelectorAll('nav button')].find(e => e.textContent.trim().startsWith(${JSON.stringify(text)}))`
async function capture(name) {
  await delay(350)
  await evaluate('document.fonts.ready.then(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))))')
  const shot = await rpc('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false })
  await writeFile(join(output, name + '.png'), Buffer.from(shot.data, 'base64'))
  report.screenshots.push(name + '.png')
}
async function viewport(width, height) {
  await rpc('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 1, mobile: width < 760 })
  await delay(300)
  const layout = await evaluate(`({width:innerWidth,document_width:document.documentElement.scrollWidth,
    font_loaded:[...document.fonts].some(f=>f.family.includes('DM Sans') && f.status==='loaded')})`)
  const name = `No page overflow at ${width}×${height}`
  if (width < 760) {
    const passed = layout.document_width <= layout.width + 1
    report.checks.push({ name, passed, details: layout })
    console.log(passed ? 'PASS:' : 'FINDING:', name)
  } else check(name, layout.document_width <= layout.width + 1, layout)
}
async function escape() {
  await rpc('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 })
  await rpc('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 })
}

await mkdir(output, { recursive: true })
try {
  const health = await localJson('/api/health', 5000)
  const overview = await localJson('/api/overview?dataset=yfs', 8000)
  check('Backend is healthy', health.status === 'ok')
  check('YFS synthetic dataset is ready', overview.records.length === 28 && overview.reference_date === '2026-10-30')
  check('Groq credentials are configured', overview.readiness.llm.configured && overview.readiness.llm.provider === 'groq')
  check('Installed Chrome and built-in WebSocket are available', chromePath && typeof WebSocket === 'function')
  if (process.argv.includes('--preflight')) {
    console.log('Preflight only. Browser interaction and screenshots have not run.')
  } else {
    const profile = join(root, '.cache', 'rehearsal', `chrome-${Date.now()}`)
    await mkdir(profile, { recursive: true })
    browser = spawn(chromePath, ['--headless', '--no-first-run', '--no-default-browser-check',
      '--disable-background-networking', '--remote-debugging-address=127.0.0.1', '--remote-debugging-port=0',
      `--user-data-dir=${profile}`, 'about:blank'], { windowsHide: true, stdio: 'ignore' })
    let launchError
    browser.on('error', error => { launchError = error.message })
    const port = await until(async () => {
      if (launchError || browser.exitCode !== null) throw new Error('Chrome could not start. Run this command from your own PowerShell terminal.')
      try { return (await readFile(join(profile, 'DevToolsActivePort'), 'utf8')).split('\n')[0].trim() } catch { return null }
    }, 15000)
    const targets = await fetch(`http://127.0.0.1:${port}/json/list`).then(r => r.json())
    socket = new WebSocket(targets.find(target => target.type === 'page').webSocketDebuggerUrl)
    await new Promise((resolve, reject) => {
      socket.addEventListener('open', resolve, { once: true })
      socket.addEventListener('error', () => reject(new Error('Could not attach to the rehearsal browser')), { once: true })
    })
    socket.addEventListener('message', async event => {
      const message = JSON.parse(event.data)
      if (message.id && pending.has(message.id)) {
        const call = pending.get(message.id); pending.delete(message.id); clearTimeout(call.timer)
        message.error ? call.reject(new Error(message.error.message)) : call.resolve(message.result)
      }
      if (message.method === 'Runtime.exceptionThrown') report.console_errors.push(message.params.exceptionDetails.text)
      if (message.method === 'Network.requestWillBeSent' && message.params.request.method === 'POST') {
        report.posts.push(new URL(message.params.request.url).pathname)
      }
      if (message.method === 'Network.requestWillBeSent' && message.params.request.method === 'GET') {
        const path = new URL(message.params.request.url).pathname
        if (path === '/api/decisions/cached') report.cached_jev_reads++
        if (path.startsWith('/api/runs/')) report.run_path = path
      }
      if (message.method === 'Fetch.requestPaused') {
        report.jev_requests_blocked++
        await rpc('Fetch.failRequest', { requestId: message.params.requestId, errorReason: 'BlockedByClient' }).catch(() => {})
      }
    })
    await rpc('Page.enable'); await rpc('Runtime.enable'); await rpc('Network.enable')
    await rpc('Fetch.enable', { patterns: [{ urlPattern: '*/api/decisions/evaluate*', requestStage: 'Request' }, ...(savedMode ? [{ urlPattern: '*/api/runs', requestStage: 'Request' }] : [])] })
    await rpc('Emulation.setDeviceMetricsOverride', { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false })
    await rpc('Page.navigate', { url: base })
    await until(() => evaluate(`document.querySelector('#dataset')?.value === 'yfs' && document.body.innerText.includes('₹300,000.00')`))
    await evaluate('document.fonts.ready')
    check('Praxis title and brand are displayed', await evaluate(`document.title.startsWith('Praxis') && document.querySelector('.brand').textContent.replace(/\\s/g,'') === 'Praxis'`))
    check('Self-hosted DM Sans is loaded', await evaluate(`[...document.fonts].some(f=>f.family.includes('DM Sans') && f.status==='loaded')`))
    check('Live KPI cards match deterministic figures', await evaluate(`document.body.innerText.includes('₹340,000.00') && document.body.innerText.includes('SYNTHETIC DEMONSTRATION DATA')`))
    check('Rules selected; no provider request on load', await evaluate(`document.querySelector('#decision-provider').value === 'rules'`) && report.posts.length === 0)
    await viewport(1440, 1000); await capture('01-overview-1440')
    await viewport(1366, 768); await evaluate('scrollTo(0,0)'); await capture('02-overview-1366')
    await viewport(390, 844); await evaluate('scrollTo(0,0)'); await capture('03-mobile-overview')
    check('Closed mobile navigation is hidden', await evaluate(`getComputedStyle(document.querySelector('.sidebar')).visibility === 'hidden'`))
    await click(`document.querySelector('[aria-label="Open navigation"]')`)
    await escape()
    check('Mobile Escape returns focus to menu toggle', await evaluate(`document.activeElement.getAttribute('aria-label') === 'Open navigation' && !document.querySelector('.sidebar.is-open')`))
    await viewport(1440, 1000)
    await click(`document.querySelector('[aria-label="View metric definitions"]')`)
    check('Metric definitions open in native evidence dialog', await evaluate(`!!document.querySelector('dialog[open]')`))
    await capture('04-metric-definitions'); await escape()
    let job
    if (savedMode) {
      await click(button('Open saved briefings'))
      await until(() => evaluate(`!!${button('Open morning briefing')}`))
      await capture('04b-saved-choices')
      await click(button('Open morning briefing'))
      await until(() => evaluate(`document.querySelectorAll('.priority-card').length === 3`))
      const saved = await localJson('/api/saved-runs?dataset=yfs', 8000)
      const morning = saved.runs.find(item => item.result.question.startsWith('Prepare my founder briefing'))
      job = { status: 'completed', dataset: 'yfs', result: morning.result, presentation: 'saved' }
      check('Saved result is explicitly labeled as historical', await evaluate(`document.body.innerText.includes('Saved real run') && document.body.innerText.includes('No new agent or decision call') && !document.body.innerText.includes('Live run complete')`))
    } else {
      await click(button('Prepare my briefing'))
      console.log('Running one real Rules/Groq briefing. Provider waits may take several minutes.')
      await until(async () => {
        const state = await evaluate(`({priorities:document.querySelectorAll('.priority-card').length,error:document.querySelector('[role="alert"]')?.innerText || ''})`)
        if (state.error) throw new Error('Briefing UI reported: ' + state.error)
        return state.priorities > 0
      }, 400000)
      job = await localJson(report.run_path, 8000)
    }
    check('Accepted briefing has ranked priorities', await evaluate(`document.querySelectorAll('.priority-card').length === 3`))
    check('School briefing uses its own evidence and deterministic metrics', job.status === 'completed' && job.dataset === 'yfs'
      && Number(job.result.metrics.exposure_by_currency.INR) === 300000
      && Number(job.result.metrics.pipeline_by_currency.INR) === 340000)
    await writeFile(join(output, 'run-result.json'), JSON.stringify(job, null, 2))
    await evaluate(`document.querySelector('.summary-panel').scrollIntoView({block:'start'})`)
    await capture(savedMode ? '05-saved-briefing' : '05-live-briefing')
    await click(`[...document.querySelectorAll('.priority-card .source-chips button')].find(e=>e.textContent.includes('INC-001'))`)
    check('Incident evidence links to its contract', await evaluate(`document.querySelector('dialog[open]').innerText.includes('CON-001')`))
    await capture('06-incident-evidence')
    await click(`[...document.querySelectorAll('dialog[open] .linked-evidence button')].find(e=>e.textContent.includes('CON-001'))`)
    await capture('07-contract-evidence'); await escape()
    await click(nav('Business updates'))
    await click(`document.querySelector('[aria-label="Search business updates"]')`)
    await rpc('Input.insertText', { text: 'FEAT-001' })
    await until(() => evaluate(`document.querySelectorAll('tbody tr').length === 1`))
    await click(`document.querySelector('tbody button')`)
    check('Feature source preserves missing deadline', await evaluate(`[...document.querySelectorAll('dialog[open] dt')].find(e=>e.textContent==='Deadline')?.nextElementSibling.textContent==='Not recorded'`))
    await capture('08-feature-evidence'); await escape()
    await click(nav('Follow-up review'))
    const postsBeforeApproval = report.posts.length
    await click(button('Approve locally'))
    await until(() => evaluate(`document.body.innerText.includes('approved locally')`))
    await capture('09-local-approval')
    await click(button('Reject'))
    await until(() => evaluate(`document.body.innerText.includes('rejected locally')`))
    check('Approve/reject changed only local state', report.posts.length === postsBeforeApproval)
    await click(nav('Execution activity'))
    check('Actual Analyst retrieval and Chief completion appear', await evaluate(`document.body.innerText.includes('get_business_updates') && document.body.innerText.includes('Chief of Staff') && document.body.innerText.includes('Briefing completed and validated')`))
    await evaluate('scrollTo(0,0)'); await capture('10-actual-execution')
    if (savedMode) {
      await click(nav('Overview'))
      const downloads = join(output, `downloads-${Date.now()}`)
      await mkdir(downloads, { recursive: true })
      await rpc('Browser.setDownloadBehavior', { behavior: 'allow', downloadPath: downloads })
      await click(`document.querySelector('.export-button')`)
      const exported = await until(async () => { try { return JSON.parse(await readFile(join(downloads, 'praxis-briefing.json'), 'utf8')) } catch { return null } })
      check('Export retains the original accepted run', exported.run_id === job.result.run_id && exported.events.length > 0)
      await click(button('Open saved briefings'))
      await until(() => evaluate(`!!${button('Open decision explanation')}`))
      await click(button('Open decision explanation'))
      check('Saved comparison opens the actual explanation question', await evaluate(`document.querySelector('#founder-question')?.value?.startsWith('Why ') || document.querySelector('textarea')?.value?.startsWith('Why ')`))
      await evaluate(`document.querySelector('.summary-panel').scrollIntoView({block:'start'})`)
      await capture('11-saved-explanation')
      await rpc('Page.reload')
      await until(() => evaluate(`!!${button('Open saved briefings')}`))
      await click(button('Open saved briefings'))
      await until(() => evaluate(`!!${button('Open morning briefing')}`))
      check('Saved school briefings survive a page refresh', await evaluate(`!!${button('Open decision explanation')}`))
      await evaluate(`(() => { const e=document.querySelector('#dataset'); Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype,'value').set.call(e,'demo'); e.dispatchEvent(new Event('change',{bubbles:true})); })()`)
      await until(() => evaluate(`document.querySelector('#dataset')?.value === 'demo' && !document.querySelector('.connection-state')`))
      await click(nav('Decision lab'))
      await until(() => evaluate(`!!${button('View saved live decision')}`))
      await click(button('View saved live decision'))
      await until(() => evaluate(`!!document.querySelector('.comparison-result')`))
      check('Saved genuine JEV result is read without evaluation', await evaluate(`document.body.innerText.includes('2.97 / 3') && document.body.innerText.includes('86.0%') && document.body.innerText.includes('No new API call for this view')`))
      await evaluate(`document.querySelector('.comparison-result').scrollIntoView({block:'center'})`)
      await capture('12-saved-jev')
      check('Entire saved rehearsal makes zero POSTs', report.posts.length === 0 && report.jev_requests_blocked === 0 && report.cached_jev_reads === 1)
    } else {
      check('Exactly one briefing POST and zero JEV calls', report.posts.length === 1 && report.posts[0] === '/api/runs' && report.jev_requests_blocked === 0)
    }
    check('No uncaught browser exceptions', report.console_errors.length === 0, report.console_errors)
    report.result = report.checks.every(check => check.passed) ? 'passed' : 'completed with findings'
  }
} catch (error) {
  report.result = 'failed'; report.error = error.message
  if (socket?.readyState === WebSocket.OPEN) await capture('failure-state').catch(() => {})
  console.error('FAIL:', error.message)
  process.exitCode = 1
} finally {
  report.finished_at = new Date().toISOString()
  if (process.argv.includes('--preflight')) report.result ||= 'preflight only; no browser rehearsal'
  await writeFile(join(output, process.argv.includes('--preflight') ? 'preflight.json' : 'report.json'), JSON.stringify(report, null, 2))
  if (socket?.readyState === WebSocket.OPEN) await rpc('Browser.close').catch(() => {})
  socket?.close()
  if (browser?.exitCode === null) browser.kill()
  console.log('Evidence:', output)
}
