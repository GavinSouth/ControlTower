import { useState } from 'react'
import { useReflection, useTripStats } from '../api/hooks'
import type { Item, Reflection, Timeline, Trip } from '../api/types'
import { ICONS, subtitle, whenLabel } from '../lib/listing'
import { favourites, isRateable, journalDays, ratedCount, statCells } from '../lib/record'
import { formatDay, formatRange, formatTime } from '../lib/time'
import { FeedbackButtons } from './FeedbackButtons'
import { HeartIcon } from './icons'
import { ReflectForm } from './ReflectForm'
import { Stars } from './Stars'
import { Button, Dialog, ErrorText } from './ui'

// The past-trip record (F3.4; design: the "Past Trip Record" canvas, ARCHITECTURE.md).
// Journal text (titles, highlight, summaries, log, reviews) uses the serif voice.

const sectionTitle = 'text-sm font-semibold tracking-wide text-stone-500 uppercase'

function Chips({ values }: { values: string[] }) {
  if (!values.length) return <span className="text-stone-500">–</span>
  return (
    <span className="flex flex-wrap gap-1.5">
      {values.map((v) => (
        <span key={v} className="rounded-full border border-stone-200 bg-stone-100 px-2.5 py-0.5 text-xs font-medium text-stone-700">
          {v}
        </span>
      ))}
    </span>
  )
}

function ReflectBanner({ title, pending, onReflect }: { title: string; pending: number; onReflect: () => void }) {
  return (
    <section aria-label="Reflect on this trip"
      className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-teal-600 bg-teal-50 p-5">
      <div className="min-w-0 flex-[1_1_320px]">
        <h2 className="text-lg font-semibold">You're back from {title}. How was it?</h2>
        <p className="mt-1 text-sm text-stone-700">
          Two minutes now keeps the memory sharp and makes future suggestions better.
          {pending > 0 && ` ${pending} ${pending === 1 ? 'item is' : 'items are'} waiting for a thumbs up or down.`}
        </p>
      </div>
      <Button onClick={onReflect}>Reflect on this trip</Button>
    </section>
  )
}

function Cover({ trip, timeline, nights, reflection }: { trip: Trip; timeline: Timeline; nights: number | null; reflection: Reflection | null }) {
  const line = [
    trip.location && `📍 ${trip.location}`,
    formatRange(timeline.first_day, timeline.last_day),
    reflection?.companions.length ? `with ${reflection.companions.join(', ')}` : null,
  ].filter(Boolean)
  return (
    <section aria-label="Cover" className="rounded-xl bg-teal-700 p-6 text-white sm:p-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="text-xs font-semibold tracking-wide text-teal-100 uppercase">
            Past trip{nights !== null && ` · ${nights} ${nights === 1 ? 'night' : 'nights'}`}
          </div>
          <h1 className="mt-2 font-serif text-4xl font-bold tracking-tight">{trip.title}</h1>
          <p className="mt-2 text-teal-50">{line.join(' · ')}</p>
        </div>
        {reflection?.rating && <Stars rating={reflection.rating} size={22} />}
      </div>
      {reflection?.highlight && (
        <figure className="mt-6 border-t border-teal-800 pt-5">
          <blockquote className="font-serif text-xl leading-relaxed">“{reflection.highlight}”</blockquote>
          <figcaption className="mt-2 text-xs font-semibold tracking-wide text-teal-100 uppercase">Highlight</figcaption>
        </figure>
      )}
    </section>
  )
}

function ReflectionPanel({ reflection, onReflect }: { reflection: Reflection | null; onReflect: () => void }) {
  if (!reflection) {
    return (
      <section aria-label="Your reflection"
        className="flex flex-col items-center gap-3 rounded-xl border border-dashed border-stone-300 p-6 text-center">
        <p className="text-stone-500">No reflection yet. Your rating, highlight, and tags will appear here.</p>
        <Button variant="secondary" onClick={onReflect}>Reflect on this trip</Button>
      </section>
    )
  }
  const wouldReturn = { true: 'Yes', false: 'No', null: 'Not sure' }[String(reflection.would_return) as 'true' | 'false' | 'null']
  return (
    <section aria-label="Your reflection" className="rounded-xl border border-stone-200 bg-white p-5">
      <div className="mb-4 flex items-center justify-between">
        <h2 className={sectionTitle}>Your reflection</h2>
        <button type="button" onClick={onReflect} className="text-sm text-teal-700 hover:underline">Edit</button>
      </div>
      <dl className="grid gap-x-6 gap-y-4 sm:grid-cols-2">
        <div>
          <dt className="text-xs text-stone-500">Rating</dt>
          <dd className="mt-1 font-medium">{reflection.rating ? `${reflection.rating} of 5` : '–'}</dd>
        </div>
        <div>
          <dt className="text-xs text-stone-500">Would you go back?</dt>
          <dd className="mt-1 font-medium">{wouldReturn}</dd>
        </div>
        <div>
          <dt className="text-xs text-stone-500">Tags</dt>
          <dd className="mt-1"><Chips values={reflection.tags} /></dd>
        </div>
        <div>
          <dt className="text-xs text-stone-500">Travelled with</dt>
          <dd className="mt-1"><Chips values={reflection.companions} /></dd>
        </div>
        {reflection.notes && (
          <div className="sm:col-span-2">
            <dt className="text-xs text-stone-500">Notes</dt>
            <dd className="mt-1 font-serif whitespace-pre-line text-stone-700">{reflection.notes}</dd>
          </div>
        )}
      </dl>
    </section>
  )
}

function kindLabel(item: Item): string {
  const kind = item.kind.charAt(0).toUpperCase() + item.kind.slice(1)
  return item.kind === 'activity' && item.category ? `${kind} · ${item.category}` : kind
}

export function TripRecord({ trip, timeline, placeName }: { trip: Trip; timeline: Timeline; placeName: (id: string | null) => string | null }) {
  const reflection = useReflection(trip.id)
  const stats = useTripStats(trip.id)
  const [reflecting, setReflecting] = useState(false)
  const reflect = () => setReflecting(true)

  if (reflection.isPending) return <p className="text-stone-500">Loading…</p>
  const mine = reflection.data ?? null
  const homeTz = timeline.home_tz
  const favs = favourites(timeline)
  const { rated, total } = ratedCount(timeline)

  return (
    <div className="space-y-6">
      <ErrorText error={reflection.error ?? stats.error} />
      {!mine && <ReflectBanner title={trip.title} pending={total - rated} onReflect={reflect} />}
      <Cover trip={trip} timeline={timeline} nights={stats.data?.nights ?? null} reflection={mine} />

      {stats.data && (
        <section aria-label="Trip stats"
          className="grid grid-cols-3 gap-px overflow-hidden rounded-xl border border-stone-200 bg-stone-100 sm:grid-cols-6">
          {statCells(stats.data).map(({ value, label }) => (
            <div key={label} className="min-w-0 bg-white px-4 py-3.5">
              <div className="text-xl font-semibold tabular-nums">{value}</div>
              <div className="truncate text-xs text-stone-500" title={label}>{label}</div>
            </div>
          ))}
        </section>
      )}

      <ReflectionPanel reflection={mine} onReflect={reflect} />

      <section aria-label="Favourite moments" className="space-y-3">
        <h2 className={sectionTitle}>Favourite moments · {favs.length}</h2>
        {favs.length ? (
          <div className="grid gap-3 sm:grid-cols-3">
            {favs.map(({ item, dayNumber }) => (
              <article key={item.id} className="flex flex-col gap-1.5 rounded-xl border border-stone-200 bg-white p-4">
                <div className="flex items-center gap-2 font-semibold">
                  <HeartIcon filled className="shrink-0 text-red-600" />
                  <span className="min-w-0">{item.title}</span>
                </div>
                <div className="text-xs text-stone-500">
                  {kindLabel(item)}{dayNumber !== null && ` · Day ${dayNumber}`}
                </div>
                {item.feedback?.review && <p className="mt-1 font-serif text-[15px] text-stone-700">“{item.feedback.review}”</p>}
              </article>
            ))}
          </div>
        ) : (
          <p className="rounded-xl border border-dashed border-stone-300 p-6 text-center text-sm text-stone-500">
            Tap the heart on anything you loved and it collects here.
          </p>
        )}
      </section>

      <section aria-label="The days" className="space-y-4">
        <div className="flex items-baseline justify-between gap-3">
          <h2 className={sectionTitle}>The days</h2>
          {total > 0 && <span className="text-sm text-stone-500">{rated} of {total} rated</span>}
        </div>
        {journalDays(timeline).map(({ day, listings }) => (
          <article key={day.local_date} aria-label={`Day ${day.number}`} className="overflow-hidden rounded-xl border border-stone-200 bg-white">
            <header className="flex items-baseline gap-3 px-5 pt-4">
              <span className="text-xs font-semibold tracking-wide text-teal-700 uppercase">Day {day.number}</span>
              <span className="font-medium">{formatDay(day.local_date)}</span>
              {day.city && <span className="text-sm text-stone-500">{day.city}</span>}
            </header>
            <div className="px-5 pt-1 pb-4">
              {day.title && <h3 className="font-serif text-xl font-semibold">{day.title}</h3>}
              {day.summary && <p className="mt-1.5 font-serif leading-relaxed whitespace-pre-line text-stone-700">{day.summary}</p>}
              {day.log.length > 0 && (
                <ul className="mt-3 space-y-0.5 border-l-2 border-teal-100 pl-3 text-sm text-stone-600">
                  {day.log.map((entry) => (
                    <li key={entry.id} className="flex gap-3">
                      <span className="w-11 shrink-0 text-stone-500 tabular-nums">{formatTime(entry.occurred_at, entry.tz)}</span>
                      <span className="font-serif">
                        <span className="font-sans text-xs tracking-wide text-stone-500 uppercase">{entry.kind.replace('_', ' ')}</span>{' '}
                        {entry.text}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
              {!day.title && !day.summary && day.log.length === 0 && (
                <p className="text-sm text-stone-500">No summary yet.</p>
              )}
            </div>
            {listings.length > 0 && (
              <ul className="divide-y divide-stone-100 border-t border-stone-100">
                {listings.map((listing) => {
                  const { item } = listing
                  const skipped = item.status === 'skipped'
                  return (
                    <li key={item.id} className="flex flex-wrap items-center gap-3 px-5 py-2.5">
                      <span className={`w-28 shrink-0 text-sm text-stone-500 tabular-nums ${skipped ? 'opacity-60' : ''}`}>
                        {whenLabel(listing, homeTz)}
                      </span>
                      <span aria-hidden className={skipped ? 'opacity-60' : ''}>{ICONS[item.kind]}</span>
                      <span className={`min-w-40 flex-1 ${skipped ? 'opacity-60' : ''}`}>
                        <span className={`block font-medium ${skipped ? 'line-through' : ''}`}>{item.title}</span>
                        <span className="block text-sm text-stone-500">{subtitle(item, placeName)}</span>
                      </span>
                      {skipped && (
                        <span className="rounded-full border border-stone-300 px-2 py-0.5 text-xs text-stone-600">skipped</span>
                      )}
                      {isRateable(item) && <FeedbackButtons itemId={item.id} title={item.title} feedback={item.feedback} />}
                      {item.feedback?.review && (
                        <p className="basis-full font-serif text-sm text-stone-600 italic sm:pl-[124px]">“{item.feedback.review}”</p>
                      )}
                    </li>
                  )
                })}
              </ul>
            )}
          </article>
        ))}
      </section>

      <Dialog open={reflecting} onClose={() => setReflecting(false)} title={`Reflect on ${trip.title}`}>
        <ReflectForm tripId={trip.id} reflection={mine} onDone={() => setReflecting(false)} />
      </Dialog>
    </div>
  )
}
