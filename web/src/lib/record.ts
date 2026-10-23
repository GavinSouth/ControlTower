// The past-trip record (F3.4): which items show where, what can be rated, stats as text.
import type { Day, Item, Listing, Timeline, TripStats } from '../api/types'

/** Same rule as the backend's stats: the kinds and statuses that get 👍/👎/♥. */
const RATEABLE_KINDS = new Set(['flight', 'stay', 'transport', 'activity'])
const UNRATEABLE_STATUSES = new Set(['idea', 'skipped', 'cancelled'])

export const isRateable = (item: Item): boolean =>
  RATEABLE_KINDS.has(item.kind) && !UNRATEABLE_STATUSES.has(item.status)

export type JournalDay = { day: Day; listings: Listing[] }

/**
 * Each item once, on the first day it appears (a 5-night stay shows on check-in day, an
 * overnight flight on the first day inside the trip). Cancelled items are left out.
 */
export function journalDays(timeline: Timeline): JournalDay[] {
  const seen = new Set<string>()
  return timeline.days.map((day) => ({
    day,
    listings: day.items.filter(({ item }) => {
      if (item.status === 'cancelled' || seen.has(item.id)) return false
      seen.add(item.id)
      return true
    }),
  }))
}

export type Favourite = { item: Item; dayNumber: number | null }

/** Items I ♥'d, in trip order, with the day they first appear on. */
export function favourites(timeline: Timeline): Favourite[] {
  const out: Favourite[] = journalDays(timeline).flatMap(({ day, listings }) =>
    listings.filter(({ item }) => item.feedback?.favourite).map(({ item }) => ({ item, dayNumber: day.number })),
  )
  for (const item of timeline.unscheduled) if (item.feedback?.favourite) out.push({ item, dayNumber: null })
  return out
}

/** "7 of 11 rated": rateable items with a 👍 or 👎. */
export function ratedCount(timeline: Timeline): { rated: number; total: number } {
  const items = journalDays(timeline).flatMap(({ listings }) => listings.map((l) => l.item)).filter(isRateable)
  return { rated: items.filter((i) => i.feedback?.verdict).length, total: items.length }
}

const capitalise = (s: string) => s.charAt(0).toUpperCase() + s.slice(1)

/** "€1,262" or "€1,262 + $890": totals per currency, never converted. */
export function formatSpend(spend: TripStats['spend']): string {
  return Object.entries(spend)
    .map(([currency, amount]) =>
      new Intl.NumberFormat('en-GB', { style: 'currency', currency, maximumFractionDigits: 0 }).format(Number(amount)),
    )
    .join(' + ')
}

const plural = (n: number, one: string, many = `${one}s`) => (n === 1 ? one : many)

/** The stats strip: six value/label cells. */
export function statCells(stats: TripStats): { value: string; label: string }[] {
  const { nights, cities, countries, flights, spend, season } = stats
  const list = (names: string[]) => (names.length ? ` · ${names.join(', ')}` : '')
  return [
    { value: nights === null ? '–' : String(nights), label: plural(nights ?? 0, 'night') },
    { value: String(cities.length), label: plural(cities.length, 'city', 'cities') + list(cities) },
    { value: String(countries.length), label: plural(countries.length, 'country', 'countries') + list(countries) },
    { value: String(flights), label: plural(flights, 'flight') },
    { value: formatSpend(spend) || '–', label: 'spent' },
    { value: season ? capitalise(season) : '–', label: 'season' },
  ]
}
