import { useState } from 'react'
import { createBrowserRouter, Link, Outlet, RouterProvider } from 'react-router'
import { TripPage } from './pages/TripPage'
import { TripsPage } from './pages/TripsPage'

function Layout() {
  return (
    <div className="min-h-screen bg-stone-50 text-stone-900">
      <header className="border-b border-stone-200 bg-white">
        <div className="mx-auto flex max-w-3xl items-center px-4 py-3">
          <Link to="/" className="flex items-center gap-2 font-semibold">
            <img src="/favicon.svg" alt="" className="h-6 w-6" />
            ControlTower
          </Link>
        </div>
      </header>
      <main className="mx-auto max-w-3xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  )
}

function NotFound() {
  return (
    <p>
      Page not found.{' '}
      <Link to="/" className="text-teal-700 hover:underline">
        Back to trips
      </Link>
    </p>
  )
}

const routes = [
  {
    element: <Layout />,
    children: [
      { path: '/', element: <TripsPage /> },
      { path: '/trips/:tripId', element: <TripPage /> },
      { path: '*', element: <NotFound /> },
    ],
  },
]

export function App() {
  // One router per mount (it reads the URL when created), so each test starts fresh.
  const [router] = useState(() => createBrowserRouter(routes))
  return <RouterProvider router={router} />
}
