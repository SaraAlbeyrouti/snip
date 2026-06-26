import { useState, type FormEvent } from 'react'

interface Props {
  onSubmit: (longUrl: string) => void
  isLoading: boolean
}

export function ShortenForm({ onSubmit, isLoading }: Props) {
  const [value, setValue] = useState('')
  const [error, setError] = useState<string | null>(null)

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const trimmed = value.trim()

    if (!trimmed) {
      setError('Please enter a URL.')
      return
    }
    if (!isValidUrl(trimmed)) {
      setError('Please enter a valid http:// or https:// URL.')
      return
    }

    setError(null)
    onSubmit(trimmed)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div className="flex gap-2">
        <input
          type="url"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Paste a long URL"
          disabled={isLoading}
          className="flex-1 px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-slate-100"
        />
        <button
          type="submit"
          disabled={isLoading || !value.trim()}
          className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:bg-slate-400 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Shortening…' : 'Shorten'}
        </button>
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
    </form>
  )
}

function isValidUrl(input: string): boolean {
  try {
    const url = new URL(input)
    return url.protocol === 'http:' || url.protocol === 'https:'
  } catch {
    return false
  }
}
