export function money(value: string | number, currency = 'USD') {
  try { return new Intl.NumberFormat('en-US', { style: 'currency', currency, minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(Number(value)) }
  catch { return `${currency} ${Number(value).toFixed(2)}` }
}
export function dateLabel(date: string, options?: Intl.DateTimeFormatOptions) {
  return new Intl.DateTimeFormat('en-US', { timeZone: 'UTC', month: 'short', day: 'numeric', ...options }).format(new Date(`${date}T12:00:00Z`))
}
export function dueLabel(date: string | null, reference: string) {
  if (!date) return 'No deadline'
  const days = Math.round((Date.parse(date) - Date.parse(reference)) / 86400000)
  return days < 0 ? `${Math.abs(days)}d overdue` : days === 0 ? 'Due today' : days === 1 ? 'Due tomorrow' : `Due in ${days} days`
}
export function initials(text: string) { return text.split(' ').map(word => word[0]).join('').slice(0, 2).toUpperCase() }
