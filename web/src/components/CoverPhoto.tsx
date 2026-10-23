import { useRef, useState } from 'react'
import { useRemoveCover, useSetCover } from '../api/hooks'
import type { Photo, Trip } from '../api/types'
import { ACCEPT, photoSrcSet, photoUrl, uploadProblem } from '../lib/photo'
import { Button, ErrorText } from './ui'

// A trip's cover photo (F3.5): the image, the scrim that keeps white text readable on it,
// and the add / change / remove controls.

/**
 * The photo filling its (relative) parent. With `scrim`, a dark gradient, heaviest at the
 * bottom where text sits, keeps white text readable on any photo. Decorative, so alt="":
 * the title next to it already says what it is.
 */
export function CoverImage({
  photo,
  sizes,
  scrim = true,
  lazy = false,
}: {
  photo: Photo
  sizes: string
  scrim?: boolean
  lazy?: boolean
}) {
  return (
    <>
      <img
        src={photoUrl(photo.id, 'md')}
        srcSet={photoSrcSet(photo)}
        sizes={sizes}
        alt=""
        loading={lazy ? 'lazy' : 'eager'}
        decoding="async"
        className="absolute inset-0 h-full w-full object-cover"
      />
      {scrim && <div aria-hidden className="absolute inset-0 bg-linear-to-t from-black/80 via-black/45 to-black/15" />}
    </>
  )
}

const overlayButton =
  'rounded-md bg-black/45 px-2.5 py-1.5 text-xs font-medium text-white backdrop-blur-sm hover:bg-black/65 disabled:opacity-60'

/**
 * Add, change, or remove a trip's cover. `overlay` sits on the cover itself (on the photo
 * or the teal fallback); `form` is the Edit trip dialog's field, with a thumbnail.
 */
export function CoverPhotoControls({ trip, variant }: { trip: Trip; variant: 'overlay' | 'form' }) {
  const input = useRef<HTMLInputElement>(null)
  const upload = useSetCover(trip.id)
  const remove = useRemoveCover(trip.id)
  const [problem, setProblem] = useState<string | null>(null)
  const busy = upload.isPending || remove.isPending
  const has = trip.cover !== null

  function choose(file: File | undefined) {
    if (input.current) input.current.value = '' // so picking the same file again still fires
    if (!file) return
    const issue = uploadProblem(file)
    setProblem(issue)
    remove.reset()
    if (!issue) upload.mutate(file)
  }

  function clear() {
    if (!confirm('Remove the cover photo?')) return
    setProblem(null)
    upload.reset()
    remove.mutate()
  }

  const pick = () => input.current?.click()
  const addLabel = upload.isPending ? 'Uploading…' : has ? 'Change photo' : 'Add cover photo'
  const error = problem ?? upload.error ?? remove.error
  const fileInput = (
    <input
      ref={input}
      type="file"
      accept={ACCEPT}
      className="hidden"
      aria-label="Cover photo file"
      onChange={(e) => choose(e.target.files?.[0])}
    />
  )

  if (variant === 'overlay') {
    return (
      <div className="flex flex-col items-end gap-2">
        <div role="group" aria-label="Cover photo" className="flex gap-1.5">
          <button type="button" className={overlayButton} disabled={busy} onClick={pick}>
            {addLabel}
          </button>
          {has && (
            <button type="button" className={overlayButton} disabled={busy} onClick={clear}>
              Remove
            </button>
          )}
        </div>
        {error && (
          <p role="alert" className="max-w-64 rounded-md bg-red-50 px-2.5 py-1.5 text-xs text-red-700">
            {error instanceof Error ? error.message : error}
          </p>
        )}
        {fileInput}
      </div>
    )
  }

  return (
    <div className="text-sm">
      <span className="mb-1 block font-medium text-stone-700">Cover photo</span>
      <div className="flex items-center gap-3">
        <div className="relative h-16 w-28 shrink-0 overflow-hidden rounded-md bg-teal-700">
          {trip.cover && (
            <img
              src={photoUrl(trip.cover.id, 'sm')}
              alt="Current cover photo"
              className="absolute inset-0 h-full w-full object-cover"
            />
          )}
        </div>
        <div role="group" aria-label="Cover photo" className="flex flex-wrap gap-2">
          <Button variant="secondary" disabled={busy} onClick={pick}>
            {addLabel}
          </Button>
          {has && (
            <Button variant="danger" disabled={busy} onClick={clear}>
              Remove
            </Button>
          )}
        </div>
      </div>
      <span className="mt-1 block text-xs text-stone-500">
        JPEG, PNG, WebP, or HEIC, up to 20 MB. Location data is removed. Saved right away.
      </span>
      {error && (
        <div className="mt-2">
          <ErrorText error={error} />
        </div>
      )}
      {fileInput}
    </div>
  )
}
