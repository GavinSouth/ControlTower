import { describe, expect, it } from 'vitest'
import { formatDay, formatRange, formatTime, utcToWallTime, wallTimeToUtc } from './time'

describe('wall time ↔ UTC', () => {
  it('converts a wall-clock time in a zone to UTC', () => {
    expect(wallTimeToUtc('2027-04-05T11:05', 'America/Los_Angeles')).toBe('2027-04-05T18:05:00.000Z')
    expect(wallTimeToUtc('2027-04-06T15:25', 'Asia/Tokyo')).toBe('2027-04-06T06:25:00.000Z')
  })

  it('round-trips through the zone', () => {
    const utc = wallTimeToUtc('2027-11-07T01:30', 'Europe/London')
    expect(utcToWallTime(utc, 'Europe/London')).toBe('2027-11-07T01:30')
  })

  it('shows the same instant as each zone’s local time', () => {
    const landing = '2027-04-06T06:25:00Z'
    expect(utcToWallTime(landing, 'Asia/Tokyo')).toBe('2027-04-06T15:25')
    expect(utcToWallTime(landing, 'America/Los_Angeles')).toBe('2027-04-05T23:25')
  })

  it('moves a time in a spring-forward gap to after the gap', () => {
    // 02:30 doesn't exist in Los Angeles on 14 Mar 2027 (clocks jump 02:00 → 03:00).
    const utc = wallTimeToUtc('2027-03-14T02:30', 'America/Los_Angeles')
    expect(utcToWallTime(utc, 'America/Los_Angeles')).toBe('2027-03-14T03:30')
  })

  it('rejects non-dates and unknown zones with a readable message', () => {
    expect(() => wallTimeToUtc('tomorrow', 'UTC')).toThrow('not a date-time')
    expect(() => wallTimeToUtc('2027-04-05T11:05', 'Mars/Base')).toThrow('unknown time zone')
    expect(() => wallTimeToUtc('2027-04-05T11:05', '')).toThrow('unknown time zone')
  })
})

describe('display', () => {
  it('formats a time in its zone, naming the zone only when it differs from home', () => {
    expect(formatTime('2027-04-06T06:25:00Z', 'Asia/Tokyo', 'Asia/Tokyo')).toBe('15:25')
    expect(formatTime('2027-04-05T18:05:00Z', 'America/Los_Angeles', 'Asia/Tokyo')).toBe('11:05 PDT')
  })

  it('formats calendar days and ranges without shifting them by a zone', () => {
    expect(formatDay('2027-04-06')).toBe('Tue 6 Apr')
    expect(formatRange('2027-04-06', '2027-04-10')).toBe('6 – 10 Apr 2027')
    expect(formatRange('2027-03-28', '2027-04-02')).toBe('28 Mar – 2 Apr 2027')
    expect(formatRange('2027-12-30', '2028-01-02')).toBe('30 Dec 2027 – 2 Jan 2028')
    expect(formatRange(null, null)).toBe('')
  })
})
