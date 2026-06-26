import { useState } from 'react'
import { ShortenForm } from './components/ShortenForm'
import { ResultCard } from './components/ResultCard'
import { ErrorBanner } from './components/ErrorBanner'
import { createShortUrl, SnipAPIError } from './api/snip'
import type { URLCreateResponse } from './types/api'

// Discriminated union: state can only be one of these four shapes.
// Eliminates impossible combinations like "loading AND showing a result".
type UiState =
  | { kind: 'idle' }
  | { kind: 'loading' }
  | { kind: 'success'; result: URLCreateResponse }
  | { kind: 'error'; message: string }

export default function App() {
  const [state, setState] = useState<UiState>({ kind: 'idle' })

  async function handleSubmit(longUrl: string) {
    setState({ kind: 'loading' })
    try {
      const result = await createShortUrl(longUrl)
      setState({ kind: 'success', result })
    } catch (err) {
      const message =
        err instanceof SnipAPIError ? err.message : 'Unexpected error.'
      setState({ kind: 'error', message })
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl space-y-6">
        <header className="text-center space-y-2">
          <h1 className="text-5xl font-bold text-slate-900 tracking-tight">
            Snip
          </h1>
          <p className="text-slate-600">
            Paste a long URL, get a short one back.
          </p>
        </header>

        <ShortenForm
          onSubmit={handleSubmit}
          isLoading={state.kind === 'loading'}
        />

        {state.kind === 'success' && <ResultCard result={state.result} />}
        {state.kind === 'error' && (
          <ErrorBanner
            message={state.message}
            onDismiss={() => setState({ kind: 'idle' })}
          />
        )}
      </div>
    </main>
  )
}
