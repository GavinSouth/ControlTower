import type { LogEntry, LogEntryCreate, LogEntryPatch, LogKind } from '../api/types'
import { utcToWallTime, wallTimeToUtc } from './time'

export const LOG_KINDS: { kind: LogKind; label: string }[] = [
  { kind: 'note', label: 'Note' },
  { kind: 'check_in', label: 'Check-in' },
  { kind: 'arrival', label: 'Arrival' },
  { kind: 'departure', label: 'Departure' },
  { kind: 'summary', label: 'Summary' },
]

/** What the log form edits: wall-clock time in `tz`, like the item form. */
export type LogFormState = {
  kind: LogKind
  when: string // "2027-04-06T20:00"
  tz: string
  text: string
  itemId: string
}

/**
 * A new entry on `day`: now if the day is today in `tz` (logging as it happens),
 * otherwise midday.
 */
export function emptyLogForm(day: string, tz: string, now = new Date()): LogFormState {
  const nowLocal = utcToWallTime(now.toISOString(), tz)
  return { kind: 'note', when: nowLocal.startsWith(day) ? nowLocal : `${day}T12:00`, tz, text: '', itemId: '' }
}

export function logFormFromEntry(entry: LogEntry): LogFormState {
  return {
    kind: entry.kind,
    when: utcToWallTime(entry.occurred_at, entry.tz),
    tz: entry.tz,
    text: entry.text ?? '',
    itemId: entry.item_id ?? '',
  }
}

/** Create omits blanks. Entries typed into the UI are always `manual` (agents use others). */
export function toLogCreateBody(form: LogFormState): LogEntryCreate {
  return {
    source: 'manual',
    kind: form.kind,
    occurred_at: wallTimeToUtc(form.when, form.tz),
    tz: form.tz,
    ...(form.text.trim() ? { text: form.text.trim() } : {}),
    ...(form.itemId ? { item_id: form.itemId } : {}),
  }
}

/** PATCH sends every field the form shows, so a blank clears it. */
export function toLogPatchBody(form: LogFormState): LogEntryPatch {
  return {
    kind: form.kind,
    occurred_at: wallTimeToUtc(form.when, form.tz),
    tz: form.tz,
    text: form.text.trim() || null,
    item_id: form.itemId || null,
  }
}
