import createClient from 'openapi-fetch'
import type { paths } from './schema'

// Every path, parameter, body, and response is typed from the backend's OpenAPI schema.
// Requests go to /api/*, which Vite's dev server proxies to FastAPI on :8000.
// (Absolute URL from the page's origin: same thing in a browser, and works under Node in tests.)
export const api = createClient<paths>({
  baseUrl: `${window.location.origin}/api`,
  // Look fetch up per request (not once at import), so tests can stub it.
  fetch: (request) => globalThis.fetch(request),
})

type ValidationIssue = { loc?: (string | number)[]; msg?: string }

/** Turn a FastAPI error body (string detail or a list of field errors) into one message. */
export function errorMessage(error: unknown): string {
  const detail = (error as { detail?: unknown } | undefined)?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return (detail as ValidationIssue[])
      .map((d) => {
        const field = d.loc?.filter((p) => p !== 'body').join('.')
        return field ? `${field}: ${d.msg}` : (d.msg ?? 'invalid')
      })
      .join('; ')
  }
  return error instanceof Error ? error.message : 'Something went wrong'
}

export class ApiError extends Error {}

/** openapi-fetch returns `{ data, error }`; TanStack Query wants a value or a thrown error. */
export function unwrap<T>(result: { data?: T; error?: unknown; response: Response }): T {
  if (result.error !== undefined || !result.response.ok) {
    throw new ApiError(errorMessage(result.error) || `HTTP ${result.response.status}`)
  }
  return result.data as T
}
