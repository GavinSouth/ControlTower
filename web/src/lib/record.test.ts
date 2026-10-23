import { describe, expect, it } from 'vitest'
import type { Item, ItemFeedback, Timeline, TripStats } from '../api/types'
import { favourites, formatSpend, journalDays, ratedCount, statCells } from './record'

const activity = (id: string, fields: Partial<Item> = {}): Item =>
  ({
    kind: 'activity',
    id,
    trip_id: 't1',
    title: id,
    status: 'done',
    planned_start: null,
    planned_end: null,
    actual_start: null,
    actual_end: null,
    effective_start: null,
    effective_end: null,
    start_tz: null,
    end_tz: null,
    place_id: null,
    to_place_id: null,
    confirmation_code: null,
    cost_amount: null,
    cost_currency: null,
    notes: null,
    category: null,
    booking_url: null,
    ticket_ref: null,
    created_at: '',
    updated_at: '',
    ...fields,
  }) as Item

const fb = (fields: Partial<ItemFeedback>): ItemFeedback => ({ verdict: null, favourite: false, review: null, updated_at: '', ...fields })

const stay = activity('Hotel', { kind: 'stay', feedback: fb({ verdict: 'up' }) } as Partial<Item>)
const tarts = activity('Tarts', { feedback: fb({ verdict: 'up', favourite: true }) })
const museum = activity('Museum', { status: 'skipped' })
const refunded = activity('Refunded', { status: 'cancelled' })
const fado = activity('Fado')

const timeline: Timeline = {
  trip_id: 't1',
  title: 'Lisbon',
  home_tz: 'Europe/Lisbon',
  first_day: '2025-05-10',
  last_day: '2025-05-11',
  phase: 'past',
  days: [
    { local_date: '2025-05-10', number: 1, title: null, city: null, summary: null, log: [],
      items: [{ role: 'starts', item: stay }, { role: 'single', item: tarts }, { role: 'single', item: refunded }] },
    { local_date: '2025-05-11', number: 2, title: null, city: null, summary: null, log: [],
      items: [{ role: 'ends', item: stay }, { role: 'single', item: museum }, { role: 'single', item: fado }] },
  ],
  unscheduled: [],
}

describe('past trip record', () => {
  it('lists each item once, on its first day, without cancelled ones', () => {
    const titles = journalDays(timeline).map((d) => d.listings.map((l) => l.item.title))
    expect(titles).toEqual([['Hotel', 'Tarts'], ['Museum', 'Fado']])
  })

  it('collects favourites with their day', () => {
    expect(favourites(timeline).map((f) => [f.item.title, f.dayNumber])).toEqual([['Tarts', 1]])
  })

  it('counts rated items, leaving out skipped ones', () => {
    expect(ratedCount(timeline)).toEqual({ rated: 2, total: 3 })
  })

  it('formats spend per currency and the stats strip', () => {
    expect(formatSpend({ EUR: '1262.40', USD: '890' })).toBe('€1,262 + US$890')
    const stats: TripStats = {
      nights: 1,
      cities: ['Lisbon', 'Sintra'],
      countries: ['PT'],
      flights: 0,
      spend: {},
      season: 'spring',
      feedback: { up: 0, down: 0, favourite: 0, skipped: 0, pending: 0 },
    }
    expect(statCells(stats)).toEqual([
      { value: '1', label: 'night' },
      { value: '2', label: 'cities · Lisbon, Sintra' },
      { value: '1', label: 'country · PT' },
      { value: '0', label: 'flights' },
      { value: '–', label: 'spent' },
      { value: 'Spring', label: 'season' },
    ])
  })
})
