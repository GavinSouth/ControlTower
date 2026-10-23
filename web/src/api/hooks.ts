import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, unwrap } from './client'
import type {
  DayWrite,
  ItemCreate,
  ItemFeedbackWrite,
  ItemPatch,
  LogEntryCreate,
  LogEntryPatch,
  PlaceCreate,
  PlacePatch,
  ReflectionWrite,
  TripCreate,
  TripPatch,
} from './types'

// Query keys: one place, so mutations invalidate exactly what they change.
export const keys = {
  trips: ['trips'] as const,
  trip: (id: string) => ['trips', id] as const,
  timeline: (id: string) => ['trips', id, 'timeline'] as const,
  reflection: (id: string) => ['trips', id, 'reflection'] as const,
  stats: (id: string) => ['trips', id, 'stats'] as const,
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

/** Upload a cover photo (multipart). The server makes a new photo each time, so URLs never go stale. */
export function useSetCover(tripId: string) {
  const invalidate = useInvalidateTrips()
  return useMutation({
    mutationFn: async (file: File) =>
      unwrap(
        await api.PUT('/trips/{trip_id}/cover', {
          params: { path: { trip_id: tripId } },
          // The schema types a file field as a string; send the real File as form data.
          body: { file: file as unknown as string },
          bodySerializer: (body) => {
            const form = new FormData()
            form.append('file', body.file as unknown as File)
            return form
          },
        }),
      ),
    onSuccess: invalidate,
  })
}

export function useRemoveCover(tripId: string) {
  const invalidate = useInvalidateTrips()
  return useMutation({
    mutationFn: async () =>
      unwrap(await api.DELETE('/trips/{trip_id}/cover', { params: { path: { trip_id: tripId } } })),
    onSuccess: invalidate,
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

/** A day's extras: PUT replaces them all, so blank fields clear. */
export function useSaveDay(tripId: string) {
  const invalidate = useInvalidateTrips()
  return useMutation({
    mutationFn: async ({ date, body }: { date: string; body: DayWrite }) =>
      unwrap(
        await api.PUT('/trips/{trip_id}/days/{local_date}', {
          params: { path: { trip_id: tripId, local_date: date } },
          body,
        }),
      ),
    onSuccess: invalidate,
  })
}

export function useCreateLogEntry(tripId: string) {
  const invalidate = useInvalidateTrips()
  return useMutation({
    mutationFn: async (body: LogEntryCreate) =>
      unwrap(await api.POST('/trips/{trip_id}/log', { params: { path: { trip_id: tripId } }, body })),
    onSuccess: invalidate,
  })
}

export function useUpdateLogEntry() {
  const invalidate = useInvalidateTrips()
  return useMutation({
    mutationFn: async ({ entryId, body }: { entryId: string; body: LogEntryPatch }) =>
      unwrap(await api.PATCH('/log/{entry_id}', { params: { path: { entry_id: entryId } }, body })),
    onSuccess: invalidate,
  })
}

export function useDeleteLogEntry() {
  const invalidate = useInvalidateTrips()
  return useMutation({
    mutationFn: async (entryId: string) =>
      unwrap(await api.DELETE('/log/{entry_id}', { params: { path: { entry_id: entryId } } })),
    onSuccess: invalidate,
  })
}

/** Place changes show up in every trip (names, zones), so refresh places and trips. */
function useInvalidatePlaces() {
  const client = useQueryClient()
  return () =>
    Promise.all([
      client.invalidateQueries({ queryKey: ['places'] }),
      client.invalidateQueries({ queryKey: keys.trips }),
    ])
}

export function useCreatePlace() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: async (body: PlaceCreate) => unwrap(await api.POST('/places', { body })),
    onSuccess: () => client.invalidateQueries({ queryKey: ['places'] }),
  })
}

export function useUpdatePlace() {
  const invalidate = useInvalidatePlaces()
  return useMutation({
    mutationFn: async ({ placeId, body }: { placeId: string; body: PlacePatch }) =>
      unwrap(await api.PATCH('/places/{place_id}', { params: { path: { place_id: placeId } }, body })),
    onSuccess: invalidate,
  })
}

export function useDeletePlace() {
  const invalidate = useInvalidatePlaces()
  return useMutation({
    mutationFn: async (placeId: string) =>
      unwrap(await api.DELETE('/places/{place_id}', { params: { path: { place_id: placeId } } })),
    onSuccess: invalidate,
  })
}

// --- Past trip record (F3.4) --------------------------------------------------

/** My reflection on a trip, or null before I've written one (the API answers 404). */
export function useReflection(tripId: string, enabled = true) {
  return useQuery({
    queryKey: keys.reflection(tripId),
    enabled,
    queryFn: async () => {
      const result = await api.GET('/trips/{trip_id}/reflection', { params: { path: { trip_id: tripId } } })
      return result.response.status === 404 ? null : unwrap(result)
    },
  })
}

/** PUT replaces the whole reflection, so fields left empty clear. */
export function useSaveReflection(tripId: string) {
  const invalidate = useInvalidateTrips()
  return useMutation({
    mutationFn: async (body: ReflectionWrite) =>
      unwrap(await api.PUT('/trips/{trip_id}/reflection', { params: { path: { trip_id: tripId } }, body })),
    onSuccess: invalidate,
  })
}

export function useTripStats(tripId: string, enabled = true) {
  return useQuery({
    queryKey: keys.stats(tripId),
    enabled,
    queryFn: async () =>
      unwrap(await api.GET('/trips/{trip_id}/stats', { params: { path: { trip_id: tripId } } })),
  })
}

/** My 👍/👎/♥ on one item. Refreshes the trip's timeline and stats (counts, favourites). */
export function useSaveFeedback() {
  const invalidate = useInvalidateTrips()
  return useMutation({
    mutationFn: async ({ itemId, body }: { itemId: string; body: ItemFeedbackWrite }) =>
      unwrap(await api.PUT('/items/{item_id}/feedback', { params: { path: { item_id: itemId } }, body })),
    onSuccess: invalidate,
  })
}
