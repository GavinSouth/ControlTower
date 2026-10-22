import { useState, type FormEvent } from 'react'
import { useCreateItem, useDeleteItem, useUpdateItem } from '../api/hooks'
import type { Item, ItemKind } from '../api/types'
import {
  DETAIL_FIELDS,
  emptyForm,
  formFromItem,
  KINDS,
  STATUSES,
  toCreateBody,
  toPatchBody,
  type ItemFormState,
} from '../lib/itemForm'
import { PlacePicker } from './PlacePicker'
import { Button, ErrorText, Field, inputClass, TimeZoneInput } from './ui'

/** Kinds that go from one place to another get a "to" place and an arrival zone. */
const TRAVELS: ItemKind[] = ['flight', 'transport']

/** Add an item to a trip (no `item`) or edit/delete one. */
export function ItemForm({
  tripId,
  homeTz,
  item,
  onDone,
}: {
  tripId: string
  homeTz: string
  item?: Item
  onDone: () => void
}) {
  const [form, setForm] = useState<ItemFormState>(() =>
    item ? formFromItem(item, homeTz) : emptyForm('activity', homeTz),
  )
  const [showActual, setShowActual] = useState(Boolean(item?.actual_start || item?.actual_end))
  const [error, setError] = useState<unknown>(null)
  const create = useCreateItem(tripId)
  const update = useUpdateItem()
  const remove = useDeleteItem()
  const set = (patch: Partial<ItemFormState>) => setForm((f) => ({ ...f, ...patch }))
  const setDetail = (name: string, value: string) =>
    setForm((f) => ({ ...f, details: { ...f.details, [name]: value } }))
  const travels = TRAVELS.includes(form.kind)

  // Errors from building the body (e.g. a bad zone) and from the server both land here.
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
      item
        ? update.mutateAsync({ itemId: item.id, body: toPatchBody(form) })
        : create.mutateAsync(toCreateBody(form)),
    )
  }

  function destroy() {
    if (item && confirm(`Delete “${item.title}”?`)) void attempt(() => remove.mutateAsync(item.id))
  }

  const timeInput = (key: 'plannedStart' | 'plannedEnd' | 'actualStart' | 'actualEnd') => (
    <input type="datetime-local" className={inputClass} value={form[key]} onChange={(e) => set({ [key]: e.target.value })} />
  )

  return (
    <form onSubmit={submit} className="space-y-4">
      {!item && (
        <div className="flex flex-wrap gap-2" role="radiogroup" aria-label="Kind">
          {KINDS.map(({ kind, label, icon }) => (
            <button
              key={kind}
              type="button"
              role="radio"
              aria-checked={form.kind === kind}
              onClick={() => set({ kind })}
              className={`rounded-full border px-3 py-1 text-sm ${
                form.kind === kind ? 'border-teal-700 bg-teal-50 text-teal-800' : 'border-stone-300 text-stone-600'
              }`}
            >
              {icon} {label}
            </button>
          ))}
        </div>
      )}

      <div className="grid grid-cols-3 gap-3">
        <div className="col-span-2">
          <Field label="Title">
            <input className={inputClass} value={form.title} required onChange={(e) => set({ title: e.target.value })} />
          </Field>
        </div>
        <Field label="Status">
          <select className={inputClass} value={form.status} onChange={(e) => set({ status: e.target.value as ItemFormState['status'] })}>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s.replace('_', ' ')}
              </option>
            ))}
          </select>
        </Field>
      </div>

      <div className={`grid gap-3 ${travels ? 'grid-cols-2' : 'grid-cols-1'}`}>
        <Field label={travels ? 'From' : 'Place'}>
          <PlacePicker
            value={form.placeId}
            defaultZone={form.startTz || homeTz}
            onChange={(place) => set({ placeId: place?.id ?? null, ...(place ? { startTz: place.tz } : {}) })}
          />
        </Field>
        {travels && (
          <Field label="To">
            <PlacePicker
              value={form.toPlaceId}
              defaultZone={form.endTz || homeTz}
              onChange={(place) => set({ toPlaceId: place?.id ?? null, ...(place ? { endTz: place.tz } : {}) })}
            />
          </Field>
        )}
      </div>

      <fieldset className="space-y-3 rounded-lg border border-stone-200 p-3">
        <legend className="px-1 text-sm font-medium text-stone-700">Planned</legend>
        <div className="grid grid-cols-2 gap-3">
          <Field label={travels ? 'Departs' : 'Starts'}>{timeInput('plannedStart')}</Field>
          <Field label={travels ? 'Arrives' : 'Ends'}>{timeInput('plannedEnd')}</Field>
          <Field label={travels ? 'Departure zone' : 'Time zone'}>
            <TimeZoneInput value={form.startTz} onChange={(startTz) => set({ startTz })} />
          </Field>
          {travels && (
            <Field label="Arrival zone" hint="Leave empty if the same">
              <TimeZoneInput value={form.endTz} onChange={(endTz) => set({ endTz })} placeholder={form.startTz} />
            </Field>
          )}
        </div>
        {!showActual ? (
          <button type="button" className="text-sm text-teal-700 hover:underline" onClick={() => setShowActual(true)}>
            + Record what actually happened
          </button>
        ) : (
          <div className="grid grid-cols-2 gap-3 border-t border-stone-200 pt-3">
            <Field label="Actually started">{timeInput('actualStart')}</Field>
            <Field label="Actually ended">{timeInput('actualEnd')}</Field>
          </div>
        )}
      </fieldset>

      {DETAIL_FIELDS[form.kind].length > 0 && (
        <div className="grid grid-cols-2 gap-3">
          {DETAIL_FIELDS[form.kind].map((field) => (
            <Field key={field.name} label={field.label}>
              {field.type === 'select' ? (
                <select className={inputClass} value={form.details[field.name] ?? ''} onChange={(e) => setDetail(field.name, e.target.value)}>
                  <option value="">—</option>
                  {field.options?.map((o) => (
                    <option key={o} value={o}>
                      {o}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  type={field.type === 'time' ? 'time' : 'text'}
                  className={inputClass}
                  value={form.details[field.name] ?? ''}
                  onChange={(e) => setDetail(field.name, e.target.value)}
                />
              )}
            </Field>
          ))}
        </div>
      )}

      <div className="grid grid-cols-3 gap-3">
        <Field label="Confirmation">
          <input className={inputClass} value={form.confirmationCode} onChange={(e) => set({ confirmationCode: e.target.value })} />
        </Field>
        <Field label="Cost">
          <input className={inputClass} inputMode="decimal" value={form.costAmount} onChange={(e) => set({ costAmount: e.target.value })} />
        </Field>
        <Field label="Currency">
          <input className={inputClass} maxLength={3} placeholder="USD" value={form.costCurrency} onChange={(e) => set({ costCurrency: e.target.value.toUpperCase() })} />
        </Field>
      </div>
      <Field label="Notes">
        <textarea className={inputClass} rows={2} value={form.notes} onChange={(e) => set({ notes: e.target.value })} />
      </Field>

      <ErrorText error={error} />
      <div className="flex justify-between">
        {item ? (
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
            {item ? 'Save' : 'Add to trip'}
          </Button>
        </div>
      </div>
    </form>
  )
}
