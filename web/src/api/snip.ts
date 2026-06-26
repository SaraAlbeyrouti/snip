import type {
  APIError,
  URLCreateRequest,
  URLCreateResponse,
} from '../types/api'

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export class SnipAPIError extends Error {
  readonly status?: number

  constructor(message: string, status?: number) {
    super(message)
    this.name = 'SnipAPIError'
    this.status = status
  }
}

export async function createShortUrl(
  longUrl: string,
): Promise<URLCreateResponse> {
  const body: URLCreateRequest = { long_url: longUrl }

  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}/api/urls`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
  } catch {
    throw new SnipAPIError('Could not reach the backend.')
  }

  if (!response.ok) {
    let message = `Request failed (${response.status})`
    try {
      const err = (await response.json()) as APIError
      if (typeof err.detail === 'string') message = err.detail
      else if (Array.isArray(err.detail) && err.detail[0]) {
        message = err.detail[0].msg
      }
    } catch {
      // Non-JSON response — keep the generic message.
    }
    throw new SnipAPIError(message, response.status)
  }

  return (await response.json()) as URLCreateResponse
}
