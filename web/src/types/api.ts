// Mirrors the backend's Pydantic schemas in app/schemas/url.py.

export interface URLCreateRequest {
  long_url: string
}

export interface URLCreateResponse {
  id: number
  short_code: string
  short_url: string
  long_url: string
  created_at: string
  click_count: number
}

// FastAPI returns `detail` as a string for plain errors and an array of issues
// for Pydantic validation errors. Our API wrapper normalizes both into one
// SnipAPIError with a friendly message.
export interface APIError {
  detail:
    | string
    | Array<{ msg: string; loc: (string | number)[]; type: string }>
}
