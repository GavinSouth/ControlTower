import { useState } from 'react'
import { useCreatePlace, usePlaces } from '../api/hooks'
import type { Place } from '../api/types'
import { ErrorText, inputClass, TimeZoneInput } from './ui'

/** Pick an existing place by name/city/IATA, or create one on the spot. */
export function PlacePicker({
  value,
  onChange,
  defaultZone,
}: {
  value: string | null
  onChange: (place: Place | null) => void
  defaultZone: string
}) {
  const [query, setQuery] = useState('')
  const [creating, setCreating] = useState(false)
  const [zone, setZone] = useState(defaultZone)
  const [iata, setIata] = useState('')
  const places = usePlaces(query)
  const all = usePlaces('')
  const createPlace = useCreatePlace()
  const selected = all.data?.find((p) => p.id === value)

  if (value) {
    return (
      <div className="flex items-center justify-between rounded-md border border-stone-300 bg-stone-50 px-3 py-2 text-sm">
        <span>
          {selected ? `${selected.name}${selected.iata_code ? ` (${selected.iata_code})` : ''}` : 'Selected place'}
          {selected && <span className="ml-2 text-xs text-stone-500">{selected.tz}</span>}
        </span>
        <button type="button" className="text-stone-500 hover:text-stone-800" onClick={() => onChange(null)}>
          Change
        </button>
      </div>
    )
  }

  if (creating) {
    return (
      <div className="space-y-2 rounded-md border border-stone-300 p-3">
        <input className={inputClass} value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Name" />
        <div className="grid grid-cols-3 gap-2">
          <div className="col-span-2">
            <TimeZoneInput value={zone} onChange={setZone} />
          </div>
          <input
            className={inputClass}
            value={iata}
            maxLength={3}
            placeholder="IATA (opt.)"
            onChange={(e) => setIata(e.target.value.toUpperCase())}
          />
        </div>
        <ErrorText error={createPlace.error} />
        <div className="flex gap-2 text-sm">
          <button
            type="button"
            className="font-medium text-teal-700 hover:underline"
            disabled={!query.trim() || createPlace.isPending}
            onClick={async () => {
              const place = await createPlace.mutateAsync({
                name: query.trim(),
                tz: zone,
                ...(iata ? { iata_code: iata } : {}),
              })
              setCreating(false)
              onChange(place)
            }}
          >
            Save place
          </button>
          <button type="button" className="text-stone-500" onClick={() => setCreating(false)}>
            Cancel
          </button>
        </div>
      </div>
    )
  }

  return (
    <div>
      <input
        className={inputClass}
        value={query}
        placeholder="Search places (name, city, IATA)…"
        onChange={(e) => setQuery(e.target.value)}
      />
      {query && (
        <ul className="mt-1 max-h-40 overflow-y-auto rounded-md border border-stone-200 text-sm">
          {places.data?.map((p) => (
            <li key={p.id}>
              <button
                type="button"
                className="w-full px-3 py-1.5 text-left hover:bg-stone-100"
                onClick={() => onChange(p)}
              >
                {p.name}
                {p.iata_code && <span className="ml-1 text-stone-500">({p.iata_code})</span>}
                {p.city && <span className="ml-2 text-xs text-stone-500">{p.city}</span>}
              </button>
            </li>
          ))}
          <li>
            <button
              type="button"
              className="w-full px-3 py-1.5 text-left font-medium text-teal-700 hover:bg-stone-100"
              onClick={() => setCreating(true)}
            >
              + New place “{query}”
            </button>
          </li>
        </ul>
      )}
    </div>
  )
}
