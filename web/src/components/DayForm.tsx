import { useState, type FormEvent } from 'react'
import { useSaveDay } from '../api/hooks'
import type { Day } from '../api/types'
import { Button, ErrorText, Field, inputClass } from './ui'

/** Edit a day's extras: a title, the city you're in, and a summary of the day. */
export function DayForm({ tripId, day, onDone }: { tripId: string; day: Day; onDone: () => void }) {
  const [title, setTitle] = useState(day.title ?? '')
  const [city, setCity] = useState(day.city ?? '')
  const [summary, setSummary] = useState(day.summary ?? '')
  const save = useSaveDay(tripId)

  async function submit(e: FormEvent) {
    e.preventDefault()
    await save.mutateAsync({
      date: day.local_date,
      body: { title: title.trim() || null, city: city.trim() || null, summary: summary.trim() || null },
    })
    onDone()
  }

  return (
    <form onSubmit={(e) => void submit(e).catch(() => {})} className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <Field label="Title">
          <input className={inputClass} value={title} maxLength={200} placeholder="e.g. Arrival" onChange={(e) => setTitle(e.target.value)} autoFocus />
        </Field>
        <Field label="City">
          <input className={inputClass} value={city} maxLength={120} placeholder="e.g. Tokyo" onChange={(e) => setCity(e.target.value)} />
        </Field>
      </div>
      <Field label="Summary" hint="How the day went, or the plan for it.">
        <textarea className={inputClass} rows={4} value={summary} onChange={(e) => setSummary(e.target.value)} />
      </Field>
      <ErrorText error={save.error} />
      <div className="flex justify-end gap-2">
        <Button variant="secondary" onClick={onDone}>
          Cancel
        </Button>
        <Button type="submit" disabled={save.isPending}>
          Save
        </Button>
      </div>
    </form>
  )
}
