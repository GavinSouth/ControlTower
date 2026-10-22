import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, unwrap } from './client'
import type { ItemCreate, ItemPatch, PlaceCreate, TripCreate, TripPatch } from './types'

// Query keys: one place, so mutations invalidate exactly what they change.
export const keys = {
  trips: ['trips'] as const,
  trip: (id: string) => ['trips', id] as const,
  timeline: (id: string) => ['trips', id, 'timeline'] as const,
  places: (q: string) => ['places', q] as const,
}

export function useTrips() {
  return useQuery({ queryKey: keys.trips, queryFn: async () => unwrap(await api.GET('/trips')) })
}

export function useTrip(tripId: string) {
  return useQuery({
    queryKey: keys.trip(tripId),
    queryFn: async () =>
      unwrap(await api.GET('/trips/{trip_id}', { params: { path: { trip_id: tripId } } })),
  })
}

export function useTimeline(tripId: string) {
  return useQuery({
    queryKey: keys.timeline(tripId),
    queryFn: async () =>
      unwrap(await api.GET('/trips/{trip_id}/timeline', { params: { path: { trip_id: tripId } } })),
  })
}

export function usePlaces(q: string) {
  return useQuery({
    queryKey: keys.places(q),
    queryFn: async () => unwrap(await api.GET('/places', { params: { query: { q, limit: 200 } } })),
  })
}

/** Invalidating ['trips'] refreshes the list, every trip, and every timeline. */
function useInvalidateTrips() {
  const client = useQueryClient()
  return () => client.invalidateQueries({ queryKey: keys.trips })
}

export function useCreateTrip() {
  const invalidate = useInvalidateTrips()
  return useMutation({
    mutationFn: async (body: TripCreate) => unwrap(await api.POST('/trips', { body })),
    onSuccess: invalidate,
  })
}

export function useUpdateTrip(tripId: string) {
  const invalidate = useInvalidateTrips()
  return useMutation({
    mutationFn: async (body: TripPatch) =>
      unwrap(await api.PATCH('/trips/{trip_id}', { params: { path: { trip_id: tripId } }, body })),
    onSuccess: invalidate,
  })
}

export function useDeleteTrip(tripId: string) {
  const client = useQueryClient()
  return useMutation({
    mutationFn: async () =>
      unwrap(await api.DELETE('/trips/{trip_id}', { params: { path: { trip_id: tripId } } })),
    onSuccess: () => {
      client.removeQueries({ queryKey: keys.trip(tripId) })
      return client.invalidateQueries({ queryKey: keys.trips, exact: true })
    },
  })
}

export function useCreateItem(tripId: string) {
  const invalidate = useInvalidateTrips()
  return useMutation({
    mutationFn: async (body: ItemCreate) =>
      unwrap(
        await api.POST('/trips/{trip_id}/items', { params: { path: { trip_id: tripId } }, body }),
      ),
    onSuccess: invalidate,
  })
}

export function useUpdateItem() {
  const invalidate = useInvalidateTrips()
  return useMutation({
    mutationFn: async ({ itemId, body }: { itemId: string; body: ItemPatch }) =>
      unwrap(await api.PATCH('/items/{item_id}', { params: { path: { item_id: itemId } }, body })),
    onSuccess: invalidate,
  })
}

export function useDeleteItem() {
  const invalidate = useInvalidateTrips()
  return useMutation({
    mutationFn: async (itemId: string) =>
      unwrap(await api.DELETE('/items/{item_id}', { params: { path: { item_id: itemId } } })),
    onSuccess: invalidate,
  })
}

export function useCreatePlace() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: async (body: PlaceCreate) => unwrap(await api.POST('/places', { body })),
    onSuccess: () => client.invalidateQueries({ queryKey: ['places'] }),
  })
}
