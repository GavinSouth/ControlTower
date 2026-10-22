import type { components, paths } from './schema'

type Schemas = components['schemas']

export type Trip = Schemas['TripRead']
export type TripCreate = Schemas['TripCreate']
export type TripPatch = Schemas['TripPatch']
export type TripPhase = Trip['phase']

export type Place = Schemas['PlaceRead']
export type PlaceCreate = Schemas['PlaceCreate']

export type Item =
  | Schemas['FlightRead']
  | Schemas['StayRead']
  | Schemas['TransportRead']
  | Schemas['ActivityRead']
  | Schemas['NoteRead']
export type ItemKind = Item['kind']
export type ItemStatus = Item['status']
export type ItemCreate =
  paths['/trips/{trip_id}/items']['post']['requestBody']['content']['application/json']
export type ItemPatch = paths['/items/{item_id}']['patch']['requestBody']['content']['application/json']

export type Timeline = Schemas['TimelineRead']
export type Day = Schemas['DayRead']
export type Listing = Schemas['ListingRead']
export type Role = Listing['role']
export type LogEntry = Schemas['LogEntryRead']
