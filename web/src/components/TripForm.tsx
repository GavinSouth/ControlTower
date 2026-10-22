import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router'
import { useCreateTrip, useDeleteTrip, useUpdateTrip } from '../api/hooks'
import type { Trip } from '../api/types'
import { browserZone } from '../lib/time'
import { Button, ErrorText, Field, inputClass, TimeZoneInput } from './ui'

/** Create a trip (no `trip`) or edit/delete an existing one. */
export function TripForm({ trip, onDone }: { trip?: Trip; onDone: () => void }) {
  const navigate = useNavigate()
  const [title, setTitle] = useState(trip?.title ?? '')
  const [homeTz, setHomeTz] = useState(trip?.home_tz ?? browserZone())
  const [startDate, setStartDate] = useState(trip?.start_date ?? '')
  const [endDate, setEndDate] = useState(trip?.end_date ?? '')
  const [notes, setNotes] = useState(trip?.notes ?? '')
  const [cancelled, setCancelled] = useState(trip?.cancelled ?? false)
  const create = useCreateTrip()
  const update = useUpdateTrip(trip?.id ?? '')
  const remove = useDeleteTrip(trip?.id ?? '')

  async function submit(e: FormEvent) {
    e.preventDefault()
    const fields = {
      title: title.trim(),
      home_tz: homeTz,
      start_date: startDate || null,
      end_date: endDate || null,
      notes: notes.trim() || null,
    }
    if (trip) {
      await update.mutateAsync({ ...fields, cancelled })
      onDone()
    } else {
      const created = await create.mutateAsync(fields)
      onDone()
      navigate(`/trips/${created.id}`)
    }
  }

  async function destroy() {
    if (!trip || !confirm(`Delete “${trip.title}” and everything in it?`)) return
    await remove.mutateAsync()
    onDone()
    navigate('/')
  }

  const error = create.error ?? update.error ?? remove.error
  return (
    <form onSubmit={(e) => void submit(e).catch(() => {})} className="space-y-4">
      <Field label="Title">
        <input className={inputClass} value={title} required onChange={(e) => setTitle(e.target.value)} autoFocus />
      </Field>
      <Field label="Home time zone" hint="Used for days without items, and for items with no place.">
        <TimeZoneInput value={homeTz} onChange={setHomeTz} required />
      </Field>
      <div className="grid grid-cols-2 gap-3">
        <Field label="Start date" hint="Optional: taken from items if empty">
          <input type="date" className={inputClass} value={startDate} onChange={(e) => setStartDate(e.target.value)} />
        </Field>
        <Field label="End date">
          <input type="date" className={inputClass} value={endDate} onChange={(e) => setEndDate(e.target.value)} />
        </Field>
      </div>
      <Field label="Notes">
        <textarea className={inputClass} rows={3} value={notes} onChange={(e) => setNotes(e.target.value)} />
      </Field>
      {trip && (
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={cancelled} onChange={(e) => setCancelled(e.target.checked)} />
          Trip cancelled
        </label>
      )}
      <ErrorText error={error} />
      <div className="flex justify-between">
        {trip ? (
          <Button variant="danger" onClick={() => void destroy().catch(() => {})}>
            Delete trip
          </Button>
        ) : (
          <span />
        )}
        <div className="flex gap-2">
          <Button variant="secondary" onClick={onDone}>
            Cancel
          </Button>
          <Button type="submit" disabled={create.isPending || update.isPending}>
            {trip ? 'Save' : 'Create trip'}
          </Button>
        </div>
      </div>
    </form>
  )
}
