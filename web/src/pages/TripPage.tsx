import { useState } from 'react'
import { Link, useParams } from 'react-router'
import { usePlaces, useTimeline, useTrip } from '../api/hooks'
import type { Day, Item, LogEntry, Timeline } from '../api/types'
import { DayCard } from '../components/DayCard'
import { DayForm } from '../components/DayForm'
import { ItemForm } from '../components/ItemForm'
import { LogForm } from '../components/LogForm'
import { TripForm } from '../components/TripForm'
import { TripRecord } from '../components/TripRecord'
import { Badge, Button, Dialog, ErrorText } from '../components/ui'
import { KINDS } from '../lib/itemForm'
import { formatRange } from '../lib/time'

type Editing =
  | { type: 'trip' }
  | { type: 'new-item' }
  | { type: 'item'; item: Item }
  | { type: 'day'; day: Day }
  | { type: 'new-log'; day: Day }
  | { type: 'log'; entry: LogEntry; day: Day }
  | null

/** Every item on the trip once (a multi-day stay is listed on each of its days). */
function tripItems(t: Timeline): Item[] {
  const byId = new Map<string, Item>()
  for (const day of t.days) for (const { item } of day.items) byId.set(item.id, item)
  for (const item of t.unscheduled) byId.set(item.id, item)
  return [...byId.values()]
}

export function TripPage() {
  const { tripId = '' } = useParams()
  const trip = useTrip(tripId)
  const timeline = useTimeline(tripId)
  const places = usePlaces('')
  const [editing, setEditing] = useState<Editing>(null)
  const [view, setView] = useState<'record' | 'plan'>('record')
  const close = () => setEditing(null)

  const placeNames = new Map(places.data?.map((p) => [p.id, p.iata_code ?? p.name]))
  const placeName = (id: string | null) => (id ? (placeNames.get(id) ?? null) : null)

  if (trip.error) {
    return (
      <div className="space-y-4">
        <ErrorText error={trip.error} />
        <Link to="/" className="text-teal-700 hover:underline">
          ← All trips
        </Link>
      </div>
    )
  }
  if (!trip.data || !timeline.data) return <p className="text-stone-500">Loading…</p>

  const t = timeline.data
  const homeTz = trip.data.home_tz
  // A past trip opens as a record; the planning view is one toggle away (F3.4).
  const isPast = t.phase === 'past' && !trip.data.cancelled
  const back = (
    <Link to="/" className="text-sm text-teal-700 hover:underline">
      ← All trips
    </Link>
  )
  const toggle = isPast && (
    <div role="group" aria-label="View" className="flex rounded-lg bg-stone-200 p-0.5">
      {(['record', 'plan'] as const).map((v) => (
        <button
          key={v}
          type="button"
          aria-pressed={view === v}
          onClick={() => setView(v)}
          className={`rounded-md px-3 py-1.5 text-sm font-medium capitalize ${
            view === v ? 'bg-white text-stone-900 shadow-sm' : 'text-stone-600 hover:text-stone-900'
          }`}
        >
          {v}
        </button>
      ))}
    </div>
  )

  if (isPast && view === 'record') {
    return (
      <div className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          {back}
          {toggle}
        </div>
        <TripRecord trip={trip.data} timeline={t} placeName={placeName} />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <div className="flex flex-wrap items-center justify-between gap-3">
          {back}
          {toggle}
        </div>
        <div className="mt-2 flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold">{trip.data.title}</h1>
            {trip.data.location && <p className="mt-1 text-stone-700">📍 {trip.data.location}</p>}
            <p className="mt-1 flex items-center gap-2 text-sm text-stone-500">
              <span>{formatRange(t.first_day, t.last_day) || 'No dates yet'}</span>
              <Badge tone={t.phase}>{trip.data.cancelled ? 'cancelled' : t.phase}</Badge>
              <span>{homeTz}</span>
            </p>
            {trip.data.notes && <p className="mt-2 max-w-prose text-sm text-stone-600">{trip.data.notes}</p>}
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => setEditing({ type: 'trip' })}>
              Edit trip
            </Button>
            <Button onClick={() => setEditing({ type: 'new-item' })}>+ Add item</Button>
          </div>
        </div>
      </div>

      <ErrorText error={timeline.error} />
      {t.days.length === 0 && t.unscheduled.length === 0 && (
        <div className="rounded-xl border border-dashed border-stone-300 p-10 text-center text-stone-500">
          Add a flight, stay, or activity with a time and the days will appear here.
        </div>
      )}

      <div className="space-y-4">
        {t.days.map((day) => (
          <DayCard
            key={day.local_date}
            day={day}
            homeTz={homeTz}
            placeName={placeName}
            onSelect={(item) => setEditing({ type: 'item', item })}
            onEditDay={(d) => setEditing({ type: 'day', day: d })}
            onSelectLog={(entry) => setEditing({ type: 'log', entry, day })}
            onAddLog={(d) => setEditing({ type: 'new-log', day: d })}
          />
        ))}
      </div>

      {t.unscheduled.length > 0 && (
        <section aria-label="Unscheduled" className="rounded-xl border border-dashed border-stone-300 p-4">
          <h2 className="mb-2 text-sm font-semibold tracking-wide text-stone-500 uppercase">Unscheduled</h2>
          <ul className="space-y-1">
            {t.unscheduled.map((item) => (
              <li key={item.id}>
                <button
                  type="button"
                  className="text-left hover:text-teal-700"
                  onClick={() => setEditing({ type: 'item', item })}
                >
                  {KINDS.find((k) => k.kind === item.kind)?.icon} {item.title}
                  <span className="ml-2 text-xs text-stone-400">{item.status}</span>
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}

      <Dialog open={editing?.type === 'trip'} onClose={close} title="Edit trip">
        <TripForm trip={trip.data} onDone={close} />
      </Dialog>
      <Dialog open={editing?.type === 'new-item'} onClose={close} title="Add to trip">
        <ItemForm tripId={tripId} homeTz={homeTz} onDone={close} />
      </Dialog>
      <Dialog open={editing?.type === 'item'} onClose={close} title="Edit item">
        {editing?.type === 'item' && (
          <ItemForm key={editing.item.id} tripId={tripId} homeTz={homeTz} item={editing.item} onDone={close} />
        )}
      </Dialog>
      <Dialog open={editing?.type === 'day'} onClose={close} title="Edit day">
        {editing?.type === 'day' && <DayForm key={editing.day.local_date} tripId={tripId} day={editing.day} onDone={close} />}
      </Dialog>
      <Dialog open={editing?.type === 'new-log' || editing?.type === 'log'} onClose={close} title="Log entry">
        {(editing?.type === 'new-log' || editing?.type === 'log') && (
          <LogForm
            key={editing.type === 'log' ? editing.entry.id : `new-${editing.day.local_date}`}
            tripId={tripId}
            day={editing.day.local_date}
            homeTz={homeTz}
            items={tripItems(t)}
            entry={editing.type === 'log' ? editing.entry : undefined}
            onDone={close}
          />
        )}
      </Dialog>
    </div>
  )
}
