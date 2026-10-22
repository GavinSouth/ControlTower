import type { components } from '../api/schema'
import type { Item, ItemCreate, ItemKind, ItemPatch, ItemStatus } from '../api/types'
import { utcToWallTime, wallTimeToUtc } from './time'

type TransportMode = NonNullable<components['schemas']['TransportCreate']['mode']>

export const KINDS: { kind: ItemKind; label: string; icon: string }[] = [
  { kind: 'flight', label: 'Flight', icon: '✈️' },
  { kind: 'stay', label: 'Stay', icon: '🛏️' },
  { kind: 'transport', label: 'Transport', icon: '🚆' },
  { kind: 'activity', label: 'Activity', icon: '📍' },
  { kind: 'note', label: 'Note', icon: '📝' },
]

export const STATUSES: ItemStatus[] = [
  'idea',
  'planned',
  'booked',
  'in_progress',
  'done',
  'skipped',
  'cancelled',
]

const MODES: TransportMode[] = [
  'train',
  'metro',
  'bus',
  'car',
  'rideshare',
  'taxi',
  'ferry',
  'bike',
  'walk',
  'other',
]

export type DetailField = {
  name: string // API field name
  label: string
  type?: 'text' | 'time' | 'select'
  options?: readonly string[]
}

/** The extra fields each kind adds (its detail table). */
export const DETAIL_FIELDS: Record<ItemKind, DetailField[]> = {
  flight: [
    { name: 'airline', label: 'Airline (IATA)' },
    { name: 'flight_number', label: 'Flight number' },
    { name: 'seat', label: 'Seat' },
    { name: 'cabin', label: 'Cabin' },
    { name: 'terminal_from', label: 'Departure terminal' },
    { name: 'terminal_to', label: 'Arrival terminal' },
    { name: 'gate', label: 'Gate' },
    { name: 'aircraft', label: 'Aircraft' },
  ],
  stay: [
    { name: 'property_name', label: 'Property' },
    { name: 'room', label: 'Room' },
    { name: 'check_in_after', label: 'Check-in from', type: 'time' },
    { name: 'check_out_before', label: 'Check-out by', type: 'time' },
    { name: 'host_contact', label: 'Host contact' },
  ],
  transport: [
    { name: 'mode', label: 'Mode', type: 'select', options: MODES },
    { name: 'carrier', label: 'Carrier' },
    { name: 'vehicle_ref', label: 'Train / vehicle' },
    { name: 'seat', label: 'Seat' },
  ],
  activity: [
    { name: 'category', label: 'Category' },
    { name: 'booking_url', label: 'Booking link' },
    { name: 'ticket_ref', label: 'Ticket ref' },
  ],
  note: [],
}

export type ItemFormState = {
  kind: ItemKind
  title: string
  status: ItemStatus
  // Wall-clock "YYYY-MM-DDTHH:mm" strings; starts are in startTz, ends in endTz.
  plannedStart: string
  plannedEnd: string
  actualStart: string
  actualEnd: string
  startTz: string
  endTz: string
  placeId: string | null
  toPlaceId: string | null
  confirmationCode: string
  costAmount: string
  costCurrency: string
  notes: string
  details: Record<string, string>
}

export function emptyForm(kind: ItemKind, homeTz: string): ItemFormState {
  return {
    kind,
    title: '',
    status: 'planned',
    plannedStart: '',
    plannedEnd: '',
    actualStart: '',
    actualEnd: '',
    startTz: homeTz,
    endTz: '',
    placeId: null,
    toPlaceId: null,
    confirmationCode: '',
    costAmount: '',
    costCurrency: '',
    notes: '',
    details: {},
  }
}

export function formFromItem(item: Item, homeTz: string): ItemFormState {
  const startTz = item.start_tz ?? homeTz
  const endTz = item.end_tz ?? ''
  const wall = (iso: string | null, zone: string) => (iso ? utcToWallTime(iso, zone) : '')
  const details: Record<string, string> = {}
  const record = item as unknown as Record<string, unknown>
  for (const field of DETAIL_FIELDS[item.kind]) {
    const value = record[field.name]
    // Times arrive as "15:00:00"; <input type="time"> wants "15:00".
    details[field.name] = value == null ? '' : field.type === 'time' ? String(value).slice(0, 5) : String(value)
  }
  return {
    kind: item.kind,
    title: item.title,
    status: item.status,
    plannedStart: wall(item.planned_start, startTz),
    plannedEnd: wall(item.planned_end, endTz || startTz),
    actualStart: wall(item.actual_start, startTz),
    actualEnd: wall(item.actual_end, endTz || startTz),
    startTz,
    endTz,
    placeId: item.place_id,
    toPlaceId: item.to_place_id,
    confirmationCode: item.confirmation_code ?? '',
    costAmount: item.cost_amount ?? '',
    costCurrency: item.cost_currency ?? '',
    notes: item.notes ?? '',
    details,
  }
}

/** All fields in API shape; empty strings become null. */
function apiFields(form: ItemFormState): Record<string, unknown> {
  const startZone = form.startTz
  const endZone = form.endTz || form.startTz
  const utc = (wall: string, zone: string) => (wall ? wallTimeToUtc(wall, zone) : null)
  const text = (value: string) => value.trim() || null
  const fields: Record<string, unknown> = {
    title: form.title.trim(),
    status: form.status,
    planned_start: utc(form.plannedStart, startZone),
    planned_end: utc(form.plannedEnd, endZone),
    actual_start: utc(form.actualStart, startZone),
    actual_end: utc(form.actualEnd, endZone),
    start_tz: text(form.startTz),
    end_tz: text(form.endTz),
    place_id: form.placeId,
    to_place_id: form.toPlaceId,
    confirmation_code: text(form.confirmationCode),
    cost_amount: text(form.costAmount),
    cost_currency: text(form.costCurrency.toUpperCase()),
    notes: text(form.notes),
  }
  for (const field of DETAIL_FIELDS[form.kind]) {
    fields[field.name] = text(form.details[field.name] ?? '')
  }
  return fields
}

/** POST body: unset fields are left out so the backend's defaults (and zone rules) apply. */
export function toCreateBody(form: ItemFormState): ItemCreate {
  const body = Object.fromEntries(Object.entries(apiFields(form)).filter(([, v]) => v !== null))
  // The server validates the exact shape for this kind (and rejects unknown fields).
  return { kind: form.kind, ...body } as ItemCreate
}

/** PATCH body: every field is sent, so emptied fields are cleared (null). */
export function toPatchBody(form: ItemFormState): ItemPatch {
  const fields = apiFields(form)
  if (form.kind === 'transport' && fields.mode === null) delete fields.mode // mode can't be null
  return { kind: form.kind, ...fields } as ItemPatch
}
