// How one item reads on one day of the timeline: icon, time label, subtitle.
import type { Item, Listing } from '../api/types'
import { KINDS } from './itemForm'
import { formatTime } from './time'

export const ICONS: Record<string, string> = Object.fromEntries(KINDS.map((k) => [k.kind, k.icon]))

/** The time text for an item on a given day, depending on its role that day. */
export function whenLabel(listing: Listing, homeTz: string): string {
  const { item, role } = listing
  const startZone = item.start_tz ?? homeTz
  const endZone = item.end_tz ?? startZone
  const start = item.effective_start && formatTime(item.effective_start, startZone, homeTz)
  const end = item.effective_end && formatTime(item.effective_end, endZone, homeTz)
  switch (role) {
    case 'single':
      return [start, end].filter(Boolean).join(' – ')
    case 'starts':
      return start ? `from ${start}` : ''
    case 'ends':
      return end ? `until ${end}` : ''
    case 'continues':
      return 'all day'
  }
}

/** "planned 18:00" when the actual time moved the item; nothing otherwise. */
export function plannedNote(item: Item, role: Listing['role'], homeTz: string): string | null {
  const startZone = item.start_tz ?? homeTz
  if (role !== 'ends' && item.actual_start && item.planned_start && item.actual_start !== item.planned_start) {
    return `planned ${formatTime(item.planned_start, startZone, homeTz)}`
  }
  if (role === 'ends' && item.actual_end && item.planned_end && item.actual_end !== item.planned_end) {
    return `planned ${formatTime(item.planned_end, item.end_tz ?? startZone, homeTz)}`
  }
  return null
}

export function subtitle(item: Item, placeName: (id: string | null) => string | null): string {
  const from = placeName(item.place_id)
  const to = placeName(item.to_place_id)
  const route = from && to ? `${from} → ${to}` : (from ?? to)
  const parts: (string | null | undefined)[] = []
  switch (item.kind) {
    case 'flight':
      parts.push([item.airline, item.flight_number].filter(Boolean).join(' ') || null, route)
      break
    case 'stay':
      parts.push(item.property_name, item.room && `room ${item.room}`, from)
      break
    case 'transport':
      parts.push(item.mode !== 'other' ? item.mode : null, item.carrier, route)
      break
    case 'activity':
      parts.push(item.category, from)
      break
    case 'note':
      parts.push(from)
  }
  return parts.filter(Boolean).join(' · ')
}
