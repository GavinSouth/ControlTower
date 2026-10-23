import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { App } from './App'
import type { Timeline, Trip } from './api/types'

const trip = (overrides: Partial<Trip>): Trip => ({
  id: 't1',
  title: 'Japan',
  location: null,
  start_date: null,
  end_date: null,
  first_day: '2027-04-05',
  last_day: '2027-04-08',
  phase: 'upcoming',
  reflection: null,
  cover: null,
  home_tz: 'Asia/Tokyo',
  cancelled: false,
  notes: null,
  created_at: '',
  updated_at: '',
  ...overrides,
})

const japan = trip({ location: 'Shinjuku, Japan' })
const lisbon = trip({ id: 't2', title: 'Lisbon', first_day: '2025-05-01', last_day: '2025-05-04', phase: 'past' })

const timeline: Timeline = {
  trip_id: 't1',
  title: 'Japan',
  home_tz: 'Asia/Tokyo',
  first_day: '2027-04-05',
  last_day: '2027-04-05',
  phase: 'upcoming',
  days: [{ local_date: '2027-04-05', number: 1, title: null, city: null, summary: null, items: [], log: [] }],
  unscheduled: [],
}

/** A fake backend: route → JSON. Records requests so tests can assert on them. */
function fakeApi(routes: Record<string, unknown>) {
  const requests: { method: string; path: string; body: unknown; contentType: string | null }[] = []
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: Request) => {
      const path = new URL(input.url).pathname.replace(/^\/api/, '')
      const contentType = input.headers.get('content-type')
      const body = contentType?.startsWith('multipart/')
        ? await input.text()
        : input.method === 'GET' || input.method === 'DELETE'
          ? undefined
          : await input.json()
      requests.push({ method: input.method, path, body, contentType })
      const key = `${input.method} ${path}`
      const data = key in routes ? routes[key] : routes[path]
      return data === undefined
        ? new Response(JSON.stringify({ detail: 'not found' }), { status: 404 })
        : new Response(JSON.stringify(data), { status: input.method === 'POST' ? 201 : 200 })
    }),
  )
  return requests
}

function renderApp(path = '/') {
  window.history.pushState({}, '', path)
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <App />
    </QueryClientProvider>,
  )
}

describe('App', () => {
  beforeEach(() => {
    // jsdom has no <dialog> methods; give it minimal ones.
    HTMLDialogElement.prototype.showModal ??= function (this: HTMLDialogElement) {
      this.open = true
    }
    HTMLDialogElement.prototype.close ??= function (this: HTMLDialogElement) {
      this.open = false
    }
  })
  afterEach(() => vi.unstubAllGlobals())

  it('lists trips grouped by phase', async () => {
    fakeApi({ '/trips': [japan, lisbon] })
    renderApp()
    const upcoming = await screen.findByRole('region', { name: 'Upcoming' })
    expect(within(upcoming).getByText('Japan')).toBeInTheDocument()
    expect(within(upcoming).getByText('5 – 8 Apr 2027')).toBeInTheDocument()
    expect(within(upcoming).getByText('📍 Shinjuku, Japan')).toBeInTheDocument()
    expect(within(screen.getByRole('region', { name: 'Past trips' })).getByText('Lisbon')).toBeInTheDocument()
  })

  it('opens a trip’s timeline', async () => {
    fakeApi({ '/trips': [japan], '/trips/t1': japan, '/trips/t1/timeline': timeline, '/places': [] })
    renderApp()
    await userEvent.click(await screen.findByText('Japan'))
    expect(await screen.findByRole('region', { name: 'Day 1' })).toHaveTextContent('Nothing planned.')
    expect(screen.getByRole('heading', { name: 'Japan' })).toBeInTheDocument()
  })

  it('creates a trip and goes to it', async () => {
    const requests = fakeApi({
      '/trips': [],
      'POST /trips': trip({ id: 'new', title: 'Kyoto', phase: 'unscheduled', first_day: null, last_day: null }),
      '/trips/new': trip({ id: 'new', title: 'Kyoto' }),
      '/trips/new/timeline': { ...timeline, trip_id: 'new', days: [] },
      '/places': [],
    })
    renderApp()
    await userEvent.click(await screen.findByText('+ New trip'))
    await userEvent.type(screen.getByLabelText('Title'), 'Kyoto')
    await userEvent.click(screen.getByText('Create trip'))

    expect(await screen.findByRole('heading', { name: 'Kyoto' })).toBeInTheDocument()
    const post = requests.find((r) => r.method === 'POST')
    expect(post?.body).toMatchObject({ title: 'Kyoto', start_date: null })
  })

  it('lists places and edits one', async () => {
    const haneda = { id: 'p1', name: 'Haneda', address: null, city: 'Tokyo', country: 'JP', lat: null, lon: null, tz: 'Asia/Tokyo', iata_code: 'HND' }
    const requests = fakeApi({ '/places': [haneda], 'PATCH /places/p1': { ...haneda, city: 'Ōta, Tokyo' }, '/trips': [] })
    renderApp('/places')
    await userEvent.click(await screen.findByText('Haneda'))
    const city = screen.getByLabelText('City')
    await userEvent.clear(city)
    await userEvent.type(city, 'Ōta, Tokyo')
    await userEvent.click(screen.getByText('Save'))

    await vi.waitFor(() => expect(requests.some((r) => r.method === 'PATCH')).toBe(true))
    expect(requests.find((r) => r.method === 'PATCH')).toMatchObject({
      path: '/places/p1',
      body: { name: 'Haneda', city: 'Ōta, Tokyo', country: 'JP', iata_code: 'HND', lat: null },
    })
  })

  it('opens a past trip as a record, rates an item, and saves a reflection', async () => {
    const pastTimeline: Timeline = {
      ...timeline,
      trip_id: 't2',
      title: 'Lisbon',
      phase: 'past',
      first_day: '2025-05-01',
      last_day: '2025-05-01',
      days: [
        {
          local_date: '2025-05-01',
          number: 1,
          title: 'Belém',
          city: 'Lisbon',
          summary: 'Warm custard tarts.',
          log: [],
          items: [
            {
              role: 'single',
              item: {
                kind: 'note', id: 'i1', trip_id: 't2', title: 'Pastéis', status: 'done',
                planned_start: '2025-05-01T10:00:00Z', planned_end: null, actual_start: null, actual_end: null,
                effective_start: '2025-05-01T10:00:00Z', effective_end: null, start_tz: 'Europe/Lisbon', end_tz: null,
                place_id: null, to_place_id: null, confirmation_code: null, cost_amount: null, cost_currency: null,
                notes: null, feedback: null, created_at: '', updated_at: '',
              },
            },
            {
              role: 'single',
              item: {
                kind: 'activity', id: 'i2', trip_id: 't2', title: 'Tram 28', status: 'done',
                planned_start: '2025-05-01T12:00:00Z', planned_end: null, actual_start: null, actual_end: null,
                effective_start: '2025-05-01T12:00:00Z', effective_end: null, start_tz: 'Europe/Lisbon', end_tz: null,
                place_id: null, to_place_id: null, confirmation_code: null, cost_amount: null, cost_currency: null,
                notes: null, category: null, booking_url: null, ticket_ref: null, feedback: null, created_at: '', updated_at: '',
              },
            },
          ],
        },
      ],
    }
    const stats = {
      nights: 0, cities: ['Lisbon'], countries: ['PT'], flights: 0, spend: { EUR: '12' }, season: 'spring',
      feedback: { up: 0, down: 0, favourite: 0, skipped: 0, pending: 1 },
    }
    const reflection = {
      trip_id: 't2', rating: 4, highlight: null, would_return: true, tags: ['food'], companions: [], notes: null,
      created_at: '', updated_at: '',
    }
    const requests = fakeApi({
      '/trips/t2': lisbon,
      '/trips/t2/timeline': pastTimeline,
      '/trips/t2/stats': stats,
      '/places': [],
      'PUT /items/i2/feedback': { verdict: 'up', favourite: false, review: null, updated_at: '' },
      'PUT /trips/t2/reflection': reflection,
    })
    renderApp('/trips/t2')

    // Not reflected yet: the prompt shows, the record is the default view.
    expect(await screen.findByRole('region', { name: 'Reflect on this trip' })).toHaveTextContent('1 item is waiting')
    expect(screen.getByRole('heading', { name: 'Lisbon' })).toBeInTheDocument()
    expect(screen.getByRole('region', { name: 'Trip stats' })).toHaveTextContent('€12')

    // Notes get no feedback buttons; activities do.
    expect(screen.queryByRole('group', { name: 'Feedback on Pastéis' })).not.toBeInTheDocument()
    await userEvent.click(within(screen.getByRole('group', { name: 'Feedback on Tram 28' })).getByLabelText('Liked it'))
    await vi.waitFor(() => expect(requests.some((r) => r.method === 'PUT')).toBe(true))
    expect(requests.find((r) => r.method === 'PUT')).toMatchObject({
      path: '/items/i2/feedback',
      body: { verdict: 'up', favourite: false, review: null },
    })

    await userEvent.click(within(screen.getByRole('region', { name: 'Reflect on this trip' })).getByText('Reflect on this trip'))
    await userEvent.click(screen.getByLabelText('4 of 5'))
    await userEvent.type(screen.getByLabelText('Tags'), 'Food{Enter}')
    await userEvent.click(screen.getByLabelText('Yes'))
    await userEvent.click(screen.getByText('Save reflection'))
    await vi.waitFor(() => expect(requests.some((r) => r.path === '/trips/t2/reflection' && r.method === 'PUT')).toBe(true))
    expect(requests.find((r) => r.path === '/trips/t2/reflection' && r.method === 'PUT')?.body).toEqual({
      rating: 4, highlight: null, would_return: true, tags: ['Food'], companions: [], notes: null,
    })

    // The planning view is one toggle away.
    await userEvent.click(screen.getByRole('button', { name: 'plan' }))
    expect(await screen.findByRole('region', { name: 'Day 1' })).toHaveTextContent('Tram 28')
  })

  it('prompts for a reflection on past trip cards, and shows stars once reflected', async () => {
    const reflected = trip({ id: 't3', title: 'Porto', phase: 'past', reflection: { rating: 5, highlight: 'Port at sunset' } })
    fakeApi({ '/trips': [lisbon, reflected] })
    renderApp()
    const past = await screen.findByRole('region', { name: 'Past trips' })
    expect(within(past).getByText('How was it? Reflect on this trip →')).toBeInTheDocument()
    expect(within(past).getByRole('img', { name: 'Rated 5 of 5' })).toBeInTheDocument()
    expect(within(past).getByText('“Port at sunset”')).toBeInTheDocument()
  })

  it('shows cover photos on trip cards, with the copy sized for the card', async () => {
    const covered = trip({ id: 't4', title: 'Kyoto', cover: { id: 'ph1', width: 2400, height: 1600 } })
    fakeApi({ '/trips': [covered, lisbon] })
    renderApp()
    await screen.findByText('Kyoto')
    const strips = screen.getAllByTestId('cover-strip')
    expect(strips).toHaveLength(1) // Lisbon has no cover: no strip
    const img = strips[0].querySelector('img')
    expect(img).toHaveAttribute('srcset', expect.stringContaining('/api/photos/ph1/sm 400w'))
    expect(img).toHaveAttribute('loading', 'lazy')
  })

  it('uploads a cover photo from the past-trip cover, as form data', async () => {
    const pastTimeline: Timeline = { ...timeline, trip_id: 't2', phase: 'past', days: [] }
    const stats = {
      nights: 0, cities: [], countries: [], flights: 0, spend: {}, season: null,
      feedback: { up: 0, down: 0, favourite: 0, skipped: 0, pending: 0 },
    }
    const covered = { ...lisbon, cover: { id: 'ph2', width: 1200, height: 800 } }
    const requests = fakeApi({
      '/trips/t2': lisbon,
      '/trips/t2/timeline': pastTimeline,
      '/trips/t2/stats': stats,
      '/places': [],
      'PUT /trips/t2/cover': covered,
    })
    renderApp('/trips/t2')

    const cover = await screen.findByRole('region', { name: 'Cover' })
    expect(within(cover).queryByRole('img')).not.toBeInTheDocument() // teal fallback
    expect(within(cover).getByText('Add cover photo')).toBeInTheDocument()

    // Too big: refused in the browser, nothing sent.
    const input = within(cover).getByLabelText('Cover photo file')
    const huge = new File(['x'], 'huge.jpg', { type: 'image/jpeg' })
    Object.defineProperty(huge, 'size', { value: 21 * 1024 * 1024 })
    await userEvent.upload(input, huge)
    expect(within(cover).getByRole('alert')).toHaveTextContent('over 20 MB')

    // The fetch under test is Node's, and its FormData only takes Node's File, not jsdom's;
    // a FormData round trip makes one (jsdom drops the name on the way; a browser keeps it).
    const form = new FormData()
    form.append('file', new Blob(['jpeg'], { type: 'image/jpeg' }), 'beach.jpg')
    await userEvent.upload(input, form.get('file') as File)
    await vi.waitFor(() => expect(requests.some((r) => r.method === 'PUT')).toBe(true))
    const put = requests.find((r) => r.method === 'PUT')
    expect(put?.path).toBe('/trips/t2/cover')
    expect(put?.contentType).toMatch(/^multipart\/form-data; boundary=/)
    expect(put?.body).toContain('Content-Disposition: form-data; name="file"')
  })
})
