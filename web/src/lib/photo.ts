import type { Photo } from '../api/types'

// Cover photos (F3.5). The API stores three WebP copies by longest edge; the browser picks
// one from `srcSet` using the width it will draw the image at (`sizes`) and the screen's
// pixel density, so a phone never downloads the 2400px copy for a 400px card.

export type PhotoSize = 'sm' | 'md' | 'lg'

const MAX_EDGE: Record<PhotoSize, number> = { sm: 400, md: 1200, lg: 2400 }

export const MAX_UPLOAD_MB = 20
export const ACCEPT = 'image/jpeg,image/png,image/webp,image/heic,image/heif,.heic,.heif'

export function photoUrl(id: string, size: PhotoSize): string {
  return `/api/photos/${id}/${size}`
}

/** `srcset` with each copy's real width. Copies of a small photo share a width, so keep one. */
export function photoSrcSet(photo: Photo): string {
  const longest = Math.max(photo.width, photo.height)
  const seen = new Set<number>()
  const parts: string[] = []
  for (const size of ['sm', 'md', 'lg'] as const) {
    const scale = Math.min(1, MAX_EDGE[size] / longest)
    const width = Math.round(photo.width * scale)
    if (seen.has(width)) continue
    seen.add(width)
    parts.push(`${photoUrl(photo.id, size)} ${width}w`)
  }
  return parts.join(', ')
}

/** A message if the file can't be uploaded, checked before sending 20 MB over the wire. */
export function uploadProblem(file: File): string | null {
  if (file.size > MAX_UPLOAD_MB * 1024 * 1024) return `That photo is over ${MAX_UPLOAD_MB} MB.`
  const heic = /\.hei[cf]$/i.test(file.name) // browsers often give HEIC an empty type
  if (!heic && file.type && !ACCEPT.split(',').includes(file.type)) {
    return 'Use a JPEG, PNG, WebP, or HEIC photo.'
  }
  return null
}
