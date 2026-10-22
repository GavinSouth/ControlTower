import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { App } from './App'
import type { Timeline, Trip } from './api/types'

const trip = (overrides: Partial<Trip>): Trip => ({
  id: 't1',
  title: 'Japan',
  start_date: null,
  end_date: null,
  first_day: '2027-04-05',
  last_day: '2027-04-08',
  phase: 'upcoming',
  home_tz: 'Asia/Tokyo',
  cancelled: false,
  notes: null,
  created_at: '',
  updated_at: '',
  ...overrides,
})

const japan = trip({})
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
  const requests: { method: string; path: string; body: unknown }[] = []
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: Request) => {
      const path = new URL(input.url).pathname.replace(/^\/api/, '')
      const body = input.method === 'GET' ? undefined : await input.json()
      requests.push({ method: input.method, path, body })
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
})
