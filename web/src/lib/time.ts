import { TZDate } from '@date-fns/tz'

// The API stores instants in UTC plus an IANA zone per end. Forms work in wall-clock time
// ("2027-04-05T11:05" from <input type="datetime-local">) in a chosen zone; these helpers
// convert between the two. Display uses Intl, which knows every zone and DST rule.

export const browserZone = (): string => Intl.DateTimeFormat().resolvedOptions().timeZone

export const allZones = (): string[] => Intl.supportedValuesOf('timeZone')

export function isZone(zone: string): boolean {
  if (!zone) return false
  try {
    new Intl.DateTimeFormat('en', { timeZone: zone })
    return true
  } catch {
    return false
  }
}

/** "2027-04-05T11:05" in America/Los_Angeles → "2027-04-05T18:05:00.000Z". */
export function wallTimeToUtc(local: string, zone: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(local)
  if (!match) throw new Error(`not a date-time: ${local}`)
  if (!isZone(zone)) throw new Error(`unknown time zone: “${zone}” (pick one from the list)`)
  const [y, mo, d, h, mi] = match.slice(1).map(Number)
  // Times in a DST gap (e.g. 02:30 on a spring-forward night) move forward an hour.
  return new Date(new TZDate(y, mo - 1, d, h, mi, zone).getTime()).toISOString()
}

/** UTC instant → "2027-04-05T11:05" in `zone`, for a datetime-local input. */
export function utcToWallTime(iso: string, zone: string): string {
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat('en-CA', {
      timeZone: zone,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hourCycle: 'h23',
    })
      .formatToParts(new Date(iso))
      .map((p) => [p.type, p.value]),
  )
  return `${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}`
}

/** "11:05" in the item's own zone, plus the zone's short name when it isn't the trip's. */
export function formatTime(iso: string, zone: string, homeZone?: string): string {
  const time = new Intl.DateTimeFormat('en-GB', {
    timeZone: zone,
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(iso))
  if (!homeZone || zone === homeZone) return time
  const name = new Intl.DateTimeFormat('en-US', { timeZone: zone, timeZoneName: 'short' })
    .formatToParts(new Date(iso))
    .find((p) => p.type === 'timeZoneName')?.value
  return name ? `${time} ${name}` : time
}

/** "2027-04-06" → "Tue 6 Apr". Calendar dates have no zone, so format them as UTC. */
export function formatDay(day: string, withYear = false): string {
  return new Intl.DateTimeFormat('en-GB', {
    timeZone: 'UTC',
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    ...(withYear ? { year: 'numeric' } : {}),
  }).format(new Date(`${day}T00:00:00Z`))
}

/** "6 – 10 Apr 2027", "28 Mar – 2 Apr 2027", or "" when undated. */
export function formatRange(first: string | null, last: string | null): string {
  if (!first || !last) return ''
  const fmt = (day: string, opts: Intl.DateTimeFormatOptions) =>
    new Intl.DateTimeFormat('en-GB', { timeZone: 'UTC', ...opts }).format(new Date(`${day}T00:00:00Z`))
  const full: Intl.DateTimeFormatOptions = { day: 'numeric', month: 'short', year: 'numeric' }
  if (first === last) return fmt(first, full)
  const sameYear = first.slice(0, 4) === last.slice(0, 4)
  const sameMonth = sameYear && first.slice(0, 7) === last.slice(0, 7)
  const start = fmt(first, sameMonth ? { day: 'numeric' } : sameYear ? { day: 'numeric', month: 'short' } : full)
  return `${start} – ${fmt(last, full)}`
}
