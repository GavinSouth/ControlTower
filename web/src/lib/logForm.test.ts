import { describe, expect, it } from 'vitest'
import type { LogEntry } from '../api/types'
import { emptyLogForm, logFormFromEntry, toLogCreateBody, toLogPatchBody } from './logForm'

const entry: LogEntry = {
  id: 'l1',
  trip_id: 't1',
  occurred_at: '2027-04-06T11:00:00Z',
  tz: 'Asia/Tokyo',
  source: 'manual',
  kind: 'check_in',
  text: 'Room is great',
  item_id: 's1',
  place_id: null,
  lat: null,
  lon: null,
  raw: null,
  created_at: '',
}

describe('log form', () => {
  it('starts at the current time on today, else at midday', () => {
    const now = new Date('2027-04-06T05:30:00Z') // 14:30 in Tokyo
    expect(emptyLogForm('2027-04-06', 'Asia/Tokyo', now).when).toBe('2027-04-06T14:30')
    expect(emptyLogForm('2027-04-07', 'Asia/Tokyo', now).when).toBe('2027-04-07T12:00')
  })

  it('round-trips an entry in its own zone', () => {
    const form = logFormFromEntry(entry)
    expect(form).toEqual({ kind: 'check_in', when: '2027-04-06T20:00', tz: 'Asia/Tokyo', text: 'Room is great', itemId: 's1' })
    expect(toLogPatchBody(form)).toEqual({
      kind: 'check_in',
      occurred_at: '2027-04-06T11:00:00.000Z',
      tz: 'Asia/Tokyo',
      text: 'Room is great',
      item_id: 's1',
    })
  })

  it('omits blanks on create and clears them on patch', () => {
    const form = { ...emptyLogForm('2027-04-07', 'Asia/Tokyo'), text: '  ' }
    expect(toLogCreateBody(form)).toEqual({ source: 'manual', kind: 'note', occurred_at: '2027-04-07T03:00:00.000Z', tz: 'Asia/Tokyo' })
    expect(toLogPatchBody(form)).toMatchObject({ text: null, item_id: null })
  })

  it('rejects an unknown zone with a readable error', () => {
    expect(() => toLogCreateBody({ ...emptyLogForm('2027-04-07', 'Asia/Tokyo'), tz: 'Tokyo' })).toThrow(/unknown time zone/)
  })
})
