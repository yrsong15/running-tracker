export const mi = (miles: number | null | undefined, digits = 1) =>
  miles === null || miles === undefined ? '–' : miles.toFixed(digits)

export function duration(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined) return '–'
  const s = Math.round(seconds)
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  return h > 0 ? `${h}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}` : `${m}:${String(sec).padStart(2, '0')}`
}

export const pace = (secondsPerMile: number | null | undefined) =>
  secondsPerMile ? `${duration(secondsPerMile)}/mi` : '–'

const parseDay = (iso: string) => new Date(`${iso.slice(0, 10)}T12:00:00`)

export const shortDate = (iso: string) => parseDay(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
export const fullDate = (iso: string) =>
  parseDay(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })

/** "Oct 12 – 18, 2026", or with both years when a week spans New Year. */
export function weekRange(startIso: string, endIso: string): string {
  const start = parseDay(startIso)
  const end = parseDay(endIso)
  if (start.getFullYear() !== end.getFullYear()) return `${fullDate(startIso)} – ${fullDate(endIso)}`
  return `${shortDate(startIso)} – ${shortDate(endIso)}, ${end.getFullYear()}`
}

export const longDate = (iso: string) =>
  parseDay(iso).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })
export const monthYear = (iso: string) => parseDay(iso).toLocaleDateString(undefined, { month: 'short', year: '2-digit' })

export function relativeTime(iso: string | null): string {
  if (!iso) return 'never'
  const then = new Date(iso.endsWith('Z') ? iso : `${iso}Z`).getTime()
  const mins = Math.round((Date.now() - then) / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins} min ago`
  const hours = Math.round(mins / 60)
  if (hours < 24) return `${hours} h ago`
  return `${Math.round(hours / 24)} d ago`
}

export const titleCase = (s: string | null | undefined) =>
  s ? s.replace(/_\d+$/, '').toLowerCase().replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()) : '–'

export const CATEGORY_LABELS = { road: 'Road', treadmill: 'Treadmill', track: 'Track', trail: 'Trail' } as const
