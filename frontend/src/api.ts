export class ApiError extends Error {
  constructor(message: string, public status: number) { super(message) }
}

export async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, { ...options, headers: { 'Content-Type': 'application/json', ...options?.headers } })
  if (!response.ok) {
    let message = `The request could not complete (${response.status}).`
    try { const body = await response.json(); if (typeof body.detail === 'string') message = body.detail } catch { /* Server may return an empty body. */ }
    throw new ApiError(message, response.status)
  }
  return response.json() as Promise<T>
}
