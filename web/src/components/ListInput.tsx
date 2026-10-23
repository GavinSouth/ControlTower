import { useState } from 'react'

/** Free-text chips: Enter (or a comma) adds one, ✕ or Backspace on an empty box removes one. */
export function ListInput({
  label,
  values,
  onChange,
  placeholder,
}: {
  label: string
  values: string[]
  onChange: (values: string[]) => void
  placeholder?: string
}) {
  const [draft, setDraft] = useState('')

  function commit() {
    const value = draft.trim()
    if (value && !values.some((v) => v.toLowerCase() === value.toLowerCase())) onChange([...values, value])
    setDraft('')
  }

  return (
    <span className="flex min-h-[38px] flex-wrap items-center gap-1.5 rounded-md border border-stone-300 bg-white px-2 py-1 shadow-sm focus-within:border-teal-600 focus-within:ring-1 focus-within:ring-teal-600">
      {values.map((value) => (
        <span key={value} className="inline-flex items-center gap-1 rounded-full border border-stone-200 bg-stone-100 px-2.5 py-0.5 text-xs font-medium text-stone-700">
          {value}
          <button type="button" aria-label={`Remove ${value}`} className="text-stone-500 hover:text-stone-900"
            onClick={() => onChange(values.filter((v) => v !== value))}>
            ✕
          </button>
        </span>
      ))}
      <input
        aria-label={label}
        value={draft}
        placeholder={placeholder}
        className="min-w-[60px] flex-1 border-0 p-0.5 text-sm outline-none"
        onChange={(e) => setDraft(e.target.value)}
        onBlur={commit}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ',') {
            e.preventDefault()
            commit()
          } else if (e.key === 'Backspace' && !draft && values.length) {
            onChange(values.slice(0, -1))
          }
        }}
      />
    </span>
  )
}
