import { StarIcon } from './icons'

const FIVE = [1, 2, 3, 4, 5]

/** A read-only 1–5 rating. Stars take the text colour, so the parent sets it. */
export function Stars({ rating, size = 14 }: { rating: number; size?: number }) {
  return (
    <span role="img" aria-label={`Rated ${rating} of 5`} className="flex gap-0.5">
      {FIVE.map((n) => (
        <StarIcon key={n} size={size} filled={n <= rating} />
      ))}
    </span>
  )
}

/** Pick 1–5 stars; picking the current rating again clears it (rating is optional). */
export function StarInput({ value, onChange }: { value: number | null; onChange: (rating: number | null) => void }) {
  return (
    <div className="flex items-center gap-1">
      {FIVE.map((n) => (
        <button
          key={n}
          type="button"
          aria-label={`${n} of 5`}
          aria-pressed={value === n}
          onClick={() => onChange(value === n ? null : n)}
          className={`inline-flex h-11 w-11 items-center justify-center rounded-md hover:bg-stone-50 ${
            value !== null && n <= value ? 'text-teal-700' : 'text-stone-400'
          }`}
        >
          <StarIcon size={28} filled={value !== null && n <= value} />
        </button>
      ))}
      <span className="ml-2 text-sm text-stone-600">{value ? `${value} of 5` : 'Not rated'}</span>
    </div>
  )
}
