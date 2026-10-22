import { describe, expect, it } from 'vitest'
import type { Item } from '../api/types'
import { emptyForm, formFromItem, toCreateBody, toPatchBody } from './itemForm'

const HOME = 'Asia/Tokyo'

describe('create body', () => {
  it('converts wall times in each end’s zone and omits empty fields', () => {
    const form = {
      ...emptyForm('flight', HOME),
      title: ' UA 837 ',
      plannedStart: '2027-04-05T11:05',
      plannedEnd: '2027-04-06T15:25',
      startTz: 'America/Los_Angeles',
      endTz: 'Asia/Tokyo',
      details: { airline: 'UA', flight_number: '837', seat: '' },
    }
    expect(toCreateBody(form)).toEqual({
      kind: 'flight',
      title: 'UA 837',
      status: 'planned',
      planned_start: '2027-04-05T18:05:00.000Z',
      planned_end: '2027-04-06T06:25:00.000Z',
      start_tz: 'America/Los_Angeles',
      end_tz: 'Asia/Tokyo',
      airline: 'UA',
      flight_number: '837',
    })
  })

  it('uses the start zone for the end when no end zone is set', () => {
    const form = {
      ...emptyForm('stay', HOME),
      title: 'Hotel X',
      plannedStart: '2027-04-06T17:00',
      plannedEnd: '2027-04-08T11:00',
    }
    const body = toCreateBody(form) as Record<string, unknown>
    expect(body.planned_end).toBe('2027-04-08T02:00:00.000Z')
    expect(body).not.toHaveProperty('end_tz')
  })

  it('only sends the fields of the chosen kind', () => {
    const form = { ...emptyForm('note', HOME), title: 'x', details: { airline: 'UA' } }
    expect(toCreateBody(form)).not.toHaveProperty('airline')
  })
})

describe('edit', () => {
  const stay = {
    kind: 'stay',
    id: 'i1',
    trip_id: 't1',
    title: 'Hotel X',
    status: 'booked',
    planned_start: '2027-04-06T08:00:00Z',
    planned_end: '2027-04-08T02:00:00Z',
    actual_start: null,
    actual_end: null,
    effective_start: '2027-04-06T08:00:00Z',
    effective_end: '2027-04-08T02:00:00Z',
    start_tz: 'Asia/Tokyo',
    end_tz: null,
    place_id: null,
    to_place_id: null,
    confirmation_code: 'ABC123',
    cost_amount: '420.00',
    cost_currency: 'USD',
    notes: null,
    created_at: '',
    updated_at: '',
    property_name: null,
    room: '1204',
    check_in_after: '15:00:00',
    check_out_before: null,
    host_contact: null,
  } satisfies Item

  it('shows stored instants as wall times in the item’s zones', () => {
    const form = formFromItem(stay, HOME)
    expect(form.plannedStart).toBe('2027-04-06T17:00')
    expect(form.plannedEnd).toBe('2027-04-08T11:00')
    expect(form.details.check_in_after).toBe('15:00')
  })

  it('sends emptied fields as null so they are cleared', () => {
    const form = { ...formFromItem(stay, HOME), confirmationCode: '', details: { room: '' } }
    const body = toPatchBody(form) as Record<string, unknown>
    expect(body.kind).toBe('stay')
    expect(body.confirmation_code).toBeNull()
    expect(body.room).toBeNull()
    expect(body.planned_start).toBe('2027-04-06T08:00:00.000Z') // unchanged times round-trip
  })

  it('never nulls a transport mode', () => {
    const form = { ...emptyForm('transport', HOME), title: 'Walk' }
    expect(toPatchBody(form)).not.toHaveProperty('mode')
  })
})
