import type { Day, Item, LogEntry } from '../api/types'
import { ICONS, plannedNote, subtitle, whenLabel } from '../lib/listing'
import { formatDay, formatTime } from '../lib/time'


const DIMMED = new Set(['cancelled', 'skipped'])

export function DayCard({
  day,
  homeTz,
  placeName,
  onSelect,
  onEditDay,
  onSelectLog,
  onAddLog,
}: {
  day: Day
  homeTz: string
  placeName: (id: string | null) => string | null
  onSelect: (item: Item) => void
  onEditDay: (day: Day) => void
  onSelectLog: (entry: LogEntry) => void
  onAddLog: (day: Day) => void
}) {
  return (
    <section aria-label={`Day ${day.number}`} className="rounded-xl border border-stone-200 bg-white">
      <header className="flex items-baseline gap-3 border-b border-stone-100 px-4 py-3">
        <span className="text-xs font-semibold tracking-wide text-teal-700 uppercase">Day {day.number}</span>
        <span className="font-medium">{formatDay(day.local_date)}</span>
        {(day.title || day.city) && (
          <span className="truncate text-sm text-stone-500">{[day.title, day.city].filter(Boolean).join(' · ')}</span>
        )}
        <button
          type="button"
          onClick={() => onEditDay(day)}
          className="ml-auto shrink-0 text-xs text-stone-400 hover:text-teal-700"
          aria-label={`Edit day ${day.number}`}
        >
          Edit day
        </button>
      </header>

      {day.summary && <p className="border-b border-stone-100 px-4 py-2 text-sm whitespace-pre-line text-stone-600">{day.summary}</p>}

      {day.items.length === 0 && (
        <p className="px-4 py-3 text-sm text-stone-400">Nothing planned.</p>
      )}

      <ul className="divide-y divide-stone-100">
        {day.items.map((listing) => {
          const { item, role } = listing
          const note = plannedNote(item, role, homeTz)
          const sub = subtitle(item, placeName)
          return (
            <li key={`${item.id}-${role}`}>
              <button
                type="button"
                onClick={() => onSelect(item)}
                className={`flex w-full gap-3 px-4 py-2.5 text-left hover:bg-stone-50 ${DIMMED.has(item.status) ? 'opacity-50' : ''}`}
              >
                <span className="w-28 shrink-0 pt-0.5 text-sm text-stone-500 tabular-nums">{whenLabel(listing, homeTz)}</span>
                <span aria-hidden className="pt-0.5">
                  {ICONS[item.kind]}
                </span>
                <span className="min-w-0 flex-1">
                  <span className={`block font-medium ${DIMMED.has(item.status) ? 'line-through' : ''}`}>
                    {item.title}
                    {role === 'continues' && <span className="ml-2 text-xs font-normal text-stone-400">continues</span>}
                  </span>
                  {sub && <span className="block truncate text-sm text-stone-500">{sub}</span>}
                </span>
                <span className="shrink-0 text-right text-xs text-stone-500">
                  {item.status !== 'planned' && <span className="block">{item.status.replace('_', ' ')}</span>}
                  {note && <span className="block text-amber-700">{note}</span>}
                </span>
              </button>
            </li>
          )
        })}
      </ul>

      <div className="border-t border-dashed border-stone-200 px-4 py-2 text-sm text-stone-600">
        {day.log.length > 0 && (
          <ul className="space-y-0.5 pb-1">
            {day.log.map((entry) => (
              <li key={entry.id}>
                <button type="button" onClick={() => onSelectLog(entry)} className="flex w-full gap-3 rounded py-0.5 text-left hover:bg-stone-50">
                  <span className="w-28 shrink-0 text-stone-400 tabular-nums">{formatTime(entry.occurred_at, entry.tz, homeTz)}</span>
                  <span>
                    <span className="text-xs tracking-wide text-stone-400 uppercase">{entry.kind.replace('_', ' ')}</span>{' '}
                    {entry.text}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
        <button type="button" onClick={() => onAddLog(day)} className="text-xs text-teal-700 hover:underline">
          + Log entry
        </button>
      </div>
    </section>
  )
}
