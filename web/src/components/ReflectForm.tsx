import { useState, type FormEvent } from 'react'
import { useSaveReflection } from '../api/hooks'
import type { Reflection } from '../api/types'
import { ListInput } from './ListInput'
import { StarInput } from './Stars'
import { Button, ErrorText, Field, inputClass } from './ui'

const WOULD_RETURN: { label: string; value: boolean | null }[] = [
  { label: 'Yes', value: true },
  { label: 'Not sure', value: null },
  { label: 'No', value: false },
]

/** Label + hint around a control that holds buttons (a <label> would hijack their clicks). */
function Group({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div className="text-sm">
      <span className="mb-1 block font-medium text-stone-700">{label}</span>
      {children}
      {hint && <span className="mt-1 block text-xs text-stone-500">{hint}</span>}
    </div>
  )
}

/** Write or rewrite my reflection on a trip. Every field is optional; saving replaces it all. */
export function ReflectForm({ tripId, reflection, onDone }: { tripId: string; reflection: Reflection | null; onDone: () => void }) {
  const [rating, setRating] = useState<number | null>(reflection?.rating ?? null)
  const [highlight, setHighlight] = useState(reflection?.highlight ?? '')
  const [wouldReturn, setWouldReturn] = useState<boolean | null>(reflection?.would_return ?? null)
  const [tags, setTags] = useState(reflection?.tags ?? [])
  const [companions, setCompanions] = useState(reflection?.companions ?? [])
  const [notes, setNotes] = useState(reflection?.notes ?? '')
  const save = useSaveReflection(tripId)

  async function submit(e: FormEvent) {
    e.preventDefault()
    await save.mutateAsync({
      rating,
      highlight: highlight.trim() || null,
      would_return: wouldReturn,
      tags,
      companions,
      notes: notes.trim() || null,
    })
    onDone()
  }

  return (
    <form onSubmit={(e) => void submit(e).catch(() => {})} className="space-y-5">
      <fieldset>
        <legend className="mb-1 text-sm font-medium text-stone-700">Rating</legend>
        <StarInput value={rating} onChange={setRating} />
      </fieldset>

      <Field label="Highlight" hint="The one moment you'd tell someone about first.">
        <textarea className={`${inputClass} font-serif`} rows={2} maxLength={500} value={highlight}
          onChange={(e) => setHighlight(e.target.value)} />
      </Field>

      <fieldset>
        <legend className="mb-1.5 text-sm font-medium text-stone-700">Would you go back?</legend>
        <div className="flex flex-wrap gap-2">
          {WOULD_RETURN.map(({ label, value }) => (
            <label key={label}
              className="cursor-pointer rounded-full border border-stone-300 px-3 py-1 text-sm text-stone-600 has-checked:border-teal-700 has-checked:bg-teal-50 has-checked:text-teal-800 has-focus-visible:ring-2 has-focus-visible:ring-teal-600">
              <input type="radio" name="would-return" className="sr-only" checked={wouldReturn === value}
                onChange={() => setWouldReturn(value)} />
              {label}
            </label>
          ))}
        </div>
      </fieldset>

      <div className="grid gap-3 sm:grid-cols-2">
        <Group label="Tags" hint="Press Enter after each one.">
          <ListInput label="Tags" values={tags} onChange={setTags} placeholder="e.g. hiking" />
        </Group>
        <Group label="Travelled with" hint="Leave empty if you went solo.">
          <ListInput label="Travelled with" values={companions} onChange={setCompanions} placeholder="e.g. Alex" />
        </Group>
      </div>

      <Field label="Notes">
        <textarea className={inputClass} rows={3} value={notes} placeholder="What would you do differently next time?"
          onChange={(e) => setNotes(e.target.value)} />
      </Field>

      <p className="rounded-md border border-stone-100 bg-stone-50 px-3 py-2.5 text-sm text-stone-600">
        Every field is optional. You can rate the items one by one on the trip page.
      </p>

      <ErrorText error={save.error} />
      <div className="flex justify-end gap-2">
        <Button variant="secondary" onClick={onDone}>Cancel</Button>
        <Button type="submit" disabled={save.isPending}>{save.isPending ? 'Saving…' : 'Save reflection'}</Button>
      </div>
    </form>
  )
}
