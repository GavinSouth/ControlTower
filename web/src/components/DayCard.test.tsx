import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import type { Day, Item } from '../api/types'
import { DayCard } from './DayCard'

const base = {
  trip_id: 't1',
  status: 'planned',
  actual_start: null,
  actual_end: null,
  place_id: null,
  to_place_id: null,
  confirmation_code: null,
  cost_amount: null,
  cost_currency: null,
  notes: null,
  created_at: '',
  updated_at: '',
} as const

const flight = {
  ...base,
  kind: 'flight',
  id: 'f1',
  title: 'UA 837',
  planned_start: '2027-04-05T18:05:00Z',
  planned_end: '2027-04-06T06:25:00Z',
  actual_start: '2027-04-05T18:52:00Z',
  effective_start: '2027-04-05T18:52:00Z',
  effective_end: '2027-04-06T06:25:00Z',
  start_tz: 'America/Los_Angeles',
  end_tz: 'Asia/Tokyo',
  place_id: 'sfo',
  to_place_id: 'hnd',
  airline: 'UA',
  flight_number: '837',
  seat: null,
  cabin: null,
  terminal_from: null,
  terminal_to: null,
  gate: null,
  aircraft: null,
  booking_source: null,
} satisfies Item

const stay = {
  ...base,
  kind: 'stay',
  id: 's1',
  title: 'Hotel X',
  status: 'cancelled',
  planned_start: '2027-04-06T08:00:00Z',
  planned_end: '2027-04-08T02:00:00Z',
  effective_start: '2027-04-06T08:00:00Z',
  effective_end: '2027-04-08T02:00:00Z',
  start_tz: 'Asia/Tokyo',
  end_tz: null,
  property_name: null,
  room: '1204',
  check_in_after: null,
  check_out_before: null,
  host_contact: null,
} satisfies Item

const day: Day = {
  local_date: '2027-04-06',
  number: 2,
  title: 'Arrival',
  city: 'Tokyo',
  summary: 'Long travel day.',
  items: [
    { role: 'ends', item: flight },
    { role: 'starts', item: stay },
  ],
  log: [
    {
      id: 'l1',
      trip_id: 't1',
      occurred_at: '2027-04-06T08:40:00Z',
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
    },
  ],
}

const places: Record<string, string> = { sfo: 'SFO', hnd: 'Haneda' }

function renderDay() {
  const handlers = { onSelect: vi.fn(), onEditDay: vi.fn(), onSelectLog: vi.fn(), onAddLog: vi.fn() }
  render(<DayCard day={day} homeTz="Asia/Tokyo" placeName={(id) => (id ? places[id] : null)} {...handlers} />)
  return handlers
}

describe('DayCard', () => {
  it('shows the day header and each item with its role-specific time', () => {
    renderDay()
    const card = screen.getByRole('region', { name: 'Day 2' })
    expect(within(card).getByText('Tue 6 Apr')).toBeInTheDocument()
    expect(within(card).getByText('Arrival · Tokyo')).toBeInTheDocument()
    expect(within(card).getByText('Long travel day.')).toBeInTheDocument()
    // The flight ends today: its arrival, in Tokyo time (the trip's zone, so no zone name).
    expect(within(card).getByText('until 15:25')).toBeInTheDocument()
    expect(within(card).getByText('UA 837 · SFO → Haneda')).toBeInTheDocument()
    expect(within(card).getByText('from 17:00')).toBeInTheDocument()
  })

  it('marks cancelled items and shows the log', () => {
    renderDay()
    expect(screen.getByText('Hotel X')).toHaveClass('line-through')
    expect(screen.getByText('cancelled')).toBeInTheDocument()
    expect(screen.getByText('Room is great')).toBeInTheDocument()
  })

  it('opens an item when clicked', async () => {
    const { onSelect } = renderDay()
    await userEvent.click(screen.getByText('UA 837'))
    expect(onSelect).toHaveBeenCalledWith(flight)
  })

  it('opens the day extras and log entries for editing', async () => {
    const { onEditDay, onSelectLog, onAddLog } = renderDay()
    await userEvent.click(screen.getByRole('button', { name: 'Edit day 2' }))
    expect(onEditDay).toHaveBeenCalledWith(day)
    await userEvent.click(screen.getByText('Room is great'))
    expect(onSelectLog).toHaveBeenCalledWith(day.log[0])
    await userEvent.click(screen.getByText('+ Log entry'))
    expect(onAddLog).toHaveBeenCalledWith(day)
  })
})
