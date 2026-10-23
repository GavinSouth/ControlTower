import { useState } from 'react'
import { Link } from 'react-router'
import { useTrips } from '../api/hooks'
import type { Trip, TripPhase } from '../api/types'
import { CoverImage } from '../components/CoverPhoto'
import { Stars } from '../components/Stars'
import { TripForm } from '../components/TripForm'
import { Badge, Button, Dialog, ErrorText } from '../components/ui'
import { formatRange } from '../lib/time'

const SECTIONS: { phase: TripPhase; title: string }[] = [
  { phase: 'current', title: 'Happening now' },
  { phase: 'upcoming', title: 'Upcoming' },
  { phase: 'unscheduled', title: 'Not scheduled yet' },
  { phase: 'past', title: 'Past trips' },
]

function TripCard({ trip }: { trip: Trip }) {
  const reflectable = trip.phase === 'past' && !trip.cancelled
  const awaiting = reflectable && !trip.reflection
  return (
    <Link
      to={`/trips/${trip.id}`}
      className={`flex flex-col overflow-hidden rounded-xl border bg-white p-4 transition hover:border-teal-600 hover:shadow-sm ${
        awaiting ? 'border-teal-600' : 'border-stone-200'
      }`}
    >
      {trip.cover && (
        <div data-testid="cover-strip" className={`relative -mx-4 -mt-4 mb-3 h-28 bg-stone-200 ${trip.cancelled ? 'opacity-50 grayscale' : ''}`}>
          <CoverImage photo={trip.cover} sizes="(min-width: 640px) 50vw, 100vw" scrim={false} lazy />
        </div>
      )}
      <div className="flex items-start justify-between gap-3">
        <h3 className={`font-semibold ${trip.cancelled ? 'text-stone-400 line-through' : ''}`}>{trip.title}</h3>
        <Badge tone={trip.phase}>{trip.cancelled ? 'cancelled' : trip.phase}</Badge>
      </div>
      {trip.location && <p className="mt-1 text-sm text-stone-700">📍 {trip.location}</p>}
      <p className="mt-1 text-sm text-stone-500">{formatRange(trip.first_day, trip.last_day) || 'No dates yet'}</p>
      {awaiting && (
        <p className="mt-3 border-t border-stone-100 pt-3 text-sm font-medium text-teal-700">How was it? Reflect on this trip →</p>
      )}
      {reflectable && trip.reflection && (trip.reflection.rating || trip.reflection.highlight) && (
        <div className="mt-3 space-y-1 border-t border-stone-100 pt-3">
          {trip.reflection.rating && (
            <span className="text-teal-700">
              <Stars rating={trip.reflection.rating} />
            </span>
          )}
          {trip.reflection.highlight && (
            <p className="truncate font-serif text-sm text-stone-600">“{trip.reflection.highlight}”</p>
          )}
        </div>
      )}
    </Link>
  )
}

export function TripsPage() {
  const trips = useTrips()
  const [creating, setCreating] = useState(false)

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Trips</h1>
        <Button onClick={() => setCreating(true)}>+ New trip</Button>
      </div>

      <ErrorText error={trips.error} />
      {trips.isPending && <p className="text-stone-500">Loading…</p>}
      {trips.data?.length === 0 && (
        <div className="rounded-xl border border-dashed border-stone-300 p-10 text-center text-stone-500">
          No trips yet. Create your first one to start planning it day by day.
        </div>
      )}

      {SECTIONS.map(({ phase, title }) => {
        const inSection = trips.data?.filter((t) => t.phase === phase) ?? []
        if (inSection.length === 0) return null
        return (
          <section key={phase} aria-label={title}>
            <h2 className="mb-3 text-sm font-semibold tracking-wide text-stone-500 uppercase">{title}</h2>
            <div className="grid gap-3 sm:grid-cols-2">
              {(phase === 'past' ? [...inSection].reverse() : inSection).map((trip) => (
                <TripCard key={trip.id} trip={trip} />
              ))}
            </div>
          </section>
        )
      })}

      <Dialog open={creating} onClose={() => setCreating(false)} title="New trip">
        <TripForm onDone={() => setCreating(false)} />
      </Dialog>
    </div>
  )
}
