import { describe, expect, it } from 'vitest'
import { photoSrcSet, photoUrl, uploadProblem } from './photo'

describe('photoSrcSet', () => {
  it('lists each copy at its real width', () => {
    expect(photoSrcSet({ id: 'p', width: 2400, height: 1600 })).toBe(
      '/api/photos/p/sm 400w, /api/photos/p/md 1200w, /api/photos/p/lg 2400w',
    )
  })

  it('scales by the longest edge, so a portrait photo is narrower', () => {
    expect(photoSrcSet({ id: 'p', width: 1600, height: 2400 })).toBe(
      '/api/photos/p/sm 267w, /api/photos/p/md 800w, /api/photos/p/lg 1600w',
    )
  })

  it('keeps one entry when the copies are the same size (a small photo is never upscaled)', () => {
    expect(photoSrcSet({ id: 'p', width: 300, height: 200 })).toBe('/api/photos/p/sm 300w')
    expect(photoSrcSet({ id: 'p', width: 900, height: 600 })).toBe('/api/photos/p/sm 400w, /api/photos/p/md 900w')
  })
})

describe('uploadProblem', () => {
  const file = (name: string, type: string, bytes = 10) => new File([new Uint8Array(bytes)], name, { type })

  it('accepts the formats the API takes, including HEIC with no type', () => {
    expect(uploadProblem(file('a.jpg', 'image/jpeg'))).toBeNull()
    expect(uploadProblem(file('a.webp', 'image/webp'))).toBeNull()
    expect(uploadProblem(file('IMG_1.HEIC', ''))).toBeNull()
  })

  it('rejects other types and files over 20 MB', () => {
    expect(uploadProblem(file('a.gif', 'image/gif'))).toMatch('JPEG, PNG, WebP, or HEIC')
    expect(uploadProblem(file('a.jpg', 'image/jpeg', 20 * 1024 * 1024 + 1))).toMatch('over 20 MB')
  })
})

it('builds URLs under the /api proxy', () => {
  expect(photoUrl('p', 'md')).toBe('/api/photos/p/md')
})
