import { describe, expect, it } from 'vitest'
import type { Place } from '../api/types'
import { emptyPlaceForm, placeFormFromPlace, toPlaceBody } from './placeForm'

describe('place form', () => {
  it('clears blanks, uppercases codes, and parses coordinates', () => {
    const form = { ...emptyPlaceForm('Asia/Tokyo'), name: ' Haneda ', country: 'jp', iataCode: 'hnd', lat: '35.55', lon: ' ' }
    expect(toPlaceBody(form)).toEqual({
      name: 'Haneda',
      tz: 'Asia/Tokyo',
      city: null,
      country: 'JP',
      address: null,
      iata_code: 'HND',
      lat: 35.55,
      lon: null,
    })
  })

  it('round-trips a place', () => {
    const place: Place = {
      id: 'p1',
      name: 'Hotel X',
      address: null,
      city: 'Tokyo',
      country: 'JP',
      lat: 35.68,
      lon: 139.7,
      tz: 'Asia/Tokyo',
      iata_code: null,
    }
    expect(toPlaceBody(placeFormFromPlace(place))).toMatchObject({ name: 'Hotel X', city: 'Tokyo', lat: 35.68, lon: 139.7 })
  })

  it('rejects a coordinate that isn’t a number', () => {
    expect(() => toPlaceBody({ ...emptyPlaceForm('UTC'), name: 'x', lat: 'north' })).toThrow(/Latitude/)
  })
})
