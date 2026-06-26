interface Props {
  message: string
  onDismiss: () => void
}

export function ErrorBanner({ message, onDismiss }: Props) {
  return (
    <div
      role="alert"
      className="p-4 bg-red-50 border border-red-200 rounded-lg flex justify-between gap-3"
    >
      <div>
        <p className="text-sm font-medium text-red-800">Something went wrong</p>
        <p className="text-sm text-red-700 mt-1">{message}</p>
      </div>
      <button
        onClick={onDismiss}
        aria-label="Dismiss"
        className="text-red-600 hover:text-red-800 text-2xl leading-none"
      >
        ×
      </button>
    </div>
  )
}
