import { useState, type FormEvent } from 'react'
import { useCreateLogEntry, useDeleteLogEntry, useUpdateLogEntry } from '../api/hooks'
import type { Item, LogEntry, LogKind } from '../api/types'
import { emptyLogForm, LOG_KINDS, logFormFromEntry, toLogCreateBody, toLogPatchBody, type LogFormState } from '../lib/logForm'
import { Button, ErrorText, Field, inputClass, TimeZoneInput } from './ui'

/** Add a log entry on `day` (no `entry`) or edit/delete one. */
export function LogForm({
  tripId,
  day,
  homeTz,
  items,
  entry,
  onDone,
}: {
  tripId: string
  day: string
  homeTz: string
  items: Item[]
  entry?: LogEntry
  onDone: () => void
}) {
  const [form, setForm] = useState<LogFormState>(() => (entry ? logFormFromEntry(entry) : emptyLogForm(day, homeTz)))
  const [error, setError] = useState<unknown>(null)
  const create = useCreateLogEntry(tripId)
  const update = useUpdateLogEntry()
  const remove = useDeleteLogEntry()
  const set = (patch: Partial<LogFormState>) => setForm((f) => ({ ...f, ...patch }))

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
      entry
        ? update.mutateAsync({ entryId: entry.id, body: toLogPatchBody(form) })
        : create.mutateAsync(toLogCreateBody(form)),
    )
  }

  function destroy() {
    if (entry && confirm('Delete this log entry?')) void attempt(() => remove.mutateAsync(entry.id))
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <Field label="Kind">
          <select className={inputClass} value={form.kind} onChange={(e) => set({ kind: e.target.value as LogKind })}>
            {LOG_KINDS.map(({ kind, label }) => (
              <option key={kind} value={kind}>
                {label}
              </option>
            ))}
          </select>
        </Field>
        <Field label="About">
          <select className={inputClass} value={form.itemId} onChange={(e) => set({ itemId: e.target.value })}>
            <option value="">— nothing in particular —</option>
            {items.map((item) => (
              <option key={item.id} value={item.id}>
                {item.title}
              </option>
            ))}
          </select>
        </Field>
        <Field label="When">
          <input type="datetime-local" className={inputClass} value={form.when} required onChange={(e) => set({ when: e.target.value })} />
        </Field>
        <Field label="Time zone">
          <TimeZoneInput value={form.tz} onChange={(tz) => set({ tz })} required />
        </Field>
      </div>
      <Field label="Text">
        <textarea className={inputClass} rows={3} value={form.text} onChange={(e) => set({ text: e.target.value })} autoFocus />
      </Field>
      {entry && entry.source !== 'manual' && <p className="text-xs text-stone-500">Recorded by: {entry.source}</p>}

      <ErrorText error={error} />
      <div className="flex justify-between">
        {entry ? (
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
            {entry ? 'Save' : 'Add to log'}
          </Button>
        </div>
      </div>
    </form>
  )
}
