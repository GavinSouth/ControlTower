import { useState, type FormEvent } from 'react'
import { useCreatePlace, useDeletePlace, useUpdatePlace } from '../api/hooks'
import type { Place } from '../api/types'
import { emptyPlaceForm, placeFormFromPlace, toPlaceBody, type PlaceFormState } from '../lib/placeForm'
import { browserZone } from '../lib/time'
import { Button, ErrorText, Field, inputClass, TimeZoneInput } from './ui'

/** Add a place (no `place`) or edit/delete one. */
export function PlaceForm({ place, onDone }: { place?: Place; onDone: () => void }) {
  const [form, setForm] = useState<PlaceFormState>(() => (place ? placeFormFromPlace(place) : emptyPlaceForm(browserZone())))
  const [error, setError] = useState<unknown>(null)
  const create = useCreatePlace()
  const update = useUpdatePlace()
  const remove = useDeletePlace()
  const set = (patch: Partial<PlaceFormState>) => setForm((f) => ({ ...f, ...patch }))
  const input = (key: keyof PlaceFormState, props: React.InputHTMLAttributes<HTMLInputElement> = {}) => (
    <input className={inputClass} value={form[key]} onChange={(e) => set({ [key]: e.target.value })} {...props} />
  )

  // Errors from building the body (e.g. a bad coordinate) and from the server both land here.
  async function attempt(action: () => Promise<unknown>) {
    setError(null)
    try {
      await action()
      onDone()
    } catch (err) {
      setError(err)
    }
  }

  function submit(e: FormEvent) {
    e.preventDefault()
    void attempt(() =>
      place ? update.mutateAsync({ placeId: place.id, body: toPlaceBody(form) }) : create.mutateAsync(toPlaceBody(form)),
    )
  }

  function destroy() {
    if (place && confirm(`Delete “${place.name}”? Items that use it keep existing, without a place.`)) {
      void attempt(() => remove.mutateAsync(place.id))
    }
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="grid grid-cols-3 gap-3">
        <div className="col-span-2">
          <Field label="Name">{input('name', { required: true, maxLength: 200, autoFocus: true })}</Field>
        </div>
        <Field label="IATA code" hint="Airports only">
          {input('iataCode', { maxLength: 3, placeholder: 'HND' })}
        </Field>
        <div className="col-span-2">
          <Field label="City">{input('city', { maxLength: 120 })}</Field>
        </div>
        <Field label="Country" hint="2-letter code">
          {input('country', { maxLength: 2, placeholder: 'JP' })}
        </Field>
      </div>
      <Field label="Address">{input('address', { maxLength: 400 })}</Field>
      <Field label="Time zone" hint="Items at this place use it.">
        <TimeZoneInput value={form.tz} onChange={(tz) => set({ tz })} required />
      </Field>
      <div className="grid grid-cols-2 gap-3">
        <Field label="Latitude">{input('lat', { inputMode: 'decimal', placeholder: '35.68' })}</Field>
        <Field label="Longitude">{input('lon', { inputMode: 'decimal', placeholder: '139.76' })}</Field>
      </div>

      <ErrorText error={error} />
      <div className="flex justify-between">
        {place ? (
          <Button variant="danger" onClick={destroy}>
            Delete
          </Button>
        ) : (
          <span />
        )}
        <div className="flex gap-2">
          <Button variant="secondary" onClick={onDone}>
            Cancel
          </Button>
          <Button type="submit" disabled={create.isPending || update.isPending}>
            {place ? 'Save' : 'Add place'}
          </Button>
        </div>
      </div>
    </form>
  )
}
