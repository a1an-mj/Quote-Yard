// Calls the Quote Yard API. In development Vite forwards /api to the backend.
const BASE = '/api/v1'

export class ApiError extends Error {
  constructor(status, detail) {
    super(typeof detail === 'string' ? detail : `Request failed (${status})`)
    this.status = status
    this.detail = detail
  }
}

export async function api(path, { method = 'GET', body, signal } = {}) {
  const response = await fetch(BASE + path, {
    method,
    signal,
    credentials: 'include',
    headers: {
      // Required by the API on anything that changes data (CSRF protection).
      ...(method === 'GET' ? {} : { 'X-Quote-Yard': '1' }),
      ...(body === undefined ? {} : { 'Content-Type': 'application/json' }),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (response.status === 204) return null
  const data = await response.json().catch(() => null)
  // A shop's login is separate, so losing it must not sign a customer out.
  if (response.status === 401 && !path.startsWith('/vendor')) window.dispatchEvent(new Event('qy:unauthorized'))
  if (!response.ok) throw new ApiError(response.status, data?.detail)
  return data
}

// Words for a person, whatever went wrong. FastAPI's 422 detail is a list of field errors.
export function errorMessage(error) {
  if (error?.status === 429) return 'Too many attempts. Please wait a little and try again.'
  if (error?.status === 422 && typeof error.detail !== 'string') return 'Please check what you entered.'
  if (error instanceof ApiError && typeof error.detail === 'string') return error.detail
  return "We couldn't reach the server. Please try again."
}
