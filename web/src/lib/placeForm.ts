import type { Place, PlaceCreate, PlacePatch } from '../api/types'

/** Every place field as the text the inputs hold. */
export type PlaceFormState = Record<'name' | 'city' | 'country' | 'address' | 'tz' | 'iataCode' | 'lat' | 'lon', string>

export const emptyPlaceForm = (tz: string): PlaceFormState => ({
  name: '',
  city: '',
  country: '',
  address: '',
  tz,
  iataCode: '',
  lat: '',
  lon: '',
})

export function placeFormFromPlace(p: Place): PlaceFormState {
  return {
    name: p.name,
    city: p.city ?? '',
    country: p.country ?? '',
    address: p.address ?? '',
    tz: p.tz,
    iataCode: p.iata_code ?? '',
    lat: p.lat?.toString() ?? '',
    lon: p.lon?.toString() ?? '',
  }
}

function coordinate(value: string, label: string): number | null {
  if (!value.trim()) return null
  const n = Number(value)
  if (!Number.isFinite(n)) throw new Error(`${label} must be a number, e.g. 35.68`)
  return n
}

/** Blank → null (clears on edit); codes are uppercased; the server checks ranges and zone. */
export function toPlaceBody(form: PlaceFormState): PlacePatch & PlaceCreate {
  const text = (v: string) => v.trim() || null
  return {
    name: form.name.trim(),
    tz: form.tz.trim(),
    city: text(form.city),
    country: text(form.country.toUpperCase()),
    address: text(form.address),
    iata_code: text(form.iataCode.toUpperCase()),
    lat: coordinate(form.lat, 'Latitude'),
    lon: coordinate(form.lon, 'Longitude'),
  }
}
