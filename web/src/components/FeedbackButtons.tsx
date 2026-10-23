import { useSaveFeedback } from '../api/hooks'
import type { ItemFeedback, Verdict } from '../api/types'
import { HeartIcon, ThumbDownIcon, ThumbUpIcon } from './icons'

const BASE = 'inline-flex h-9 w-9 items-center justify-center rounded-md border transition-colors disabled:opacity-60'
const OFF = 'border-stone-300 bg-white text-stone-500 hover:bg-stone-50'
// User's choice (F3.4): 👍 teal like the rest of the app; 👎 and ♥ red.
const ON = {
  up: 'border-teal-600 bg-teal-50 text-teal-800',
  down: 'border-red-300 bg-red-50 text-red-700',
  favourite: 'border-red-300 bg-red-50 text-red-600',
}

/**
 * 👍/👎/♥ on one item. 👍 and 👎 are one verdict (picking one clears the other; picking the
 * same again clears it). ♥ is independent. Each click PUTs the whole feedback, keeping the review.
 */
export function FeedbackButtons({ itemId, title, feedback }: { itemId: string; title: string; feedback: ItemFeedback | null | undefined }) {
  const save = useSaveFeedback()
  const verdict = feedback?.verdict ?? null
  const favourite = feedback?.favourite ?? false

  const send = (next: { verdict: Verdict | null; favourite: boolean }) =>
    save.mutate({ itemId, body: { ...next, review: feedback?.review ?? null } })

  const pick = (v: Verdict) => send({ verdict: verdict === v ? null : v, favourite })

  return (
    <div role="group" aria-label={`Feedback on ${title}`} className="flex gap-1.5">
      <button type="button" aria-label="Liked it" aria-pressed={verdict === 'up'} disabled={save.isPending}
        onClick={() => pick('up')} className={`${BASE} ${verdict === 'up' ? ON.up : OFF}`}>
        <ThumbUpIcon />
      </button>
      <button type="button" aria-label="Didn't like it" aria-pressed={verdict === 'down'} disabled={save.isPending}
        onClick={() => pick('down')} className={`${BASE} ${verdict === 'down' ? ON.down : OFF}`}>
        <ThumbDownIcon />
      </button>
      <button type="button" aria-label="Favourite" aria-pressed={favourite} disabled={save.isPending}
        onClick={() => send({ verdict, favourite: !favourite })} className={`${BASE} ${favourite ? ON.favourite : OFF}`}>
        <HeartIcon filled={favourite} />
      </button>
    </div>
  )
}
