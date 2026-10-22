import { useState } from 'react'
import { usePlaces } from '../api/hooks'
import type { Place } from '../api/types'
import { PlaceForm } from '../components/PlaceForm'
import { Button, Dialog, ErrorText, inputClass } from '../components/ui'

type Editing = { type: 'new' } | { type: 'place'; place: Place } | null

/** Saved places (airports, hotels, sights), shared by every trip. */
export function PlacesPage() {
  const [query, setQuery] = useState('')
  const places = usePlaces(query)
  const [editing, setEditing] = useState<Editing>(null)
  const close = () => setEditing(null)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Places</h1>
        <Button onClick={() => setEditing({ type: 'new' })}>+ New place</Button>
      </div>

      <input
        className={inputClass}
        value={query}
        placeholder="Search by name, city, or IATA code…"
        aria-label="Search places"
        onChange={(e) => setQuery(e.target.value)}
      />

      <ErrorText error={places.error} />
      {places.isPending && <p className="text-stone-500">Loading…</p>}
      {places.data?.length === 0 && (
        <div className="rounded-xl border border-dashed border-stone-300 p-10 text-center text-stone-500">
          {query ? `No places match “${query}”.` : 'No places yet. They’re also created when you pick one on an item.'}
        </div>
      )}

      {places.data && places.data.length > 0 && (
        <ul className="divide-y divide-stone-100 rounded-xl border border-stone-200 bg-white">
          {places.data.map((place) => (
            <li key={place.id}>
              <button
                type="button"
                onClick={() => setEditing({ type: 'place', place })}
                className="flex w-full items-baseline gap-3 px-4 py-2.5 text-left hover:bg-stone-50"
              >
                <span className="min-w-0 flex-1">
                  <span className="font-medium">{place.name}</span>
                  {place.iata_code && <span className="ml-2 text-sm text-stone-500">{place.iata_code}</span>}
                  {(place.city || place.country) && (
                    <span className="block truncate text-sm text-stone-500">
                      {[place.city, place.country].filter(Boolean).join(', ')}
                    </span>
                  )}
                </span>
                <span className="shrink-0 text-xs text-stone-400">{place.tz}</span>
              </button>
            </li>
          ))}
        </ul>
      )}

      <Dialog open={editing?.type === 'new'} onClose={close} title="New place">
        <PlaceForm onDone={close} />
      </Dialog>
      <Dialog open={editing?.type === 'place'} onClose={close} title="Edit place">
        {editing?.type === 'place' && <PlaceForm key={editing.place.id} place={editing.place} onDone={close} />}
      </Dialog>
    </div>
  )
}
