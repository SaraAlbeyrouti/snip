import { useState } from 'react'
import type { URLCreateResponse } from '../types/api'

interface Props {
  result: URLCreateResponse
}

export function ResultCard({ result }: Props) {
  const [copied, setCopied] = useState(false)

  async function handleCopy() {
    await navigator.clipboard.writeText(result.short_url)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="p-4 bg-green-50 border border-green-200 rounded-lg space-y-3">
      <p className="text-sm text-slate-600">Your short URL:</p>
      <div className="flex gap-2 items-center">
        <a
          href={result.short_url}
          target="_blank"
          rel="noreferrer"
          className="flex-1 px-3 py-2 bg-white border border-slate-300 rounded font-mono text-blue-700 hover:underline truncate"
        >
          {result.short_url}
        </a>
        <button
          onClick={handleCopy}
          className="px-4 py-2 bg-slate-800 text-white text-sm font-medium rounded hover:bg-slate-700 min-w-[80px]"
        >
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>
      <p className="text-xs text-slate-500 truncate">
        Points to: {result.long_url}
      </p>
    </div>
  )
}
