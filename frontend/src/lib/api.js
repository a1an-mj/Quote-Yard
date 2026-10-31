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
  if (!response.ok) throw new ApiError(response.status, data?.detail)
  return data
}
