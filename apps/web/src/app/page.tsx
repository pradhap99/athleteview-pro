import Link from 'next/link';

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center gap-6 px-6">
      <header className="space-y-3">
        <h1 className="text-2xl font-semibold tracking-tight text-fg">
          Throughline — one live production graph
        </h1>
        <p className="max-w-xl text-fg-muted">
          Script, breakdown, schedule, Day-Out-of-Days, and budget as a single
          living graph. AI drafts every artifact; humans confirm. Every edit
          ripples through as a reviewable diff.
        </p>
      </header>

      <div className="flex items-center gap-3">
        <Link
          href="/board"
          className="inline-flex items-center rounded-md bg-accent px-4 py-2 text-sm font-medium text-accent-fg transition-opacity hover:opacity-90"
        >
          Open stripboard →
        </Link>
        <span className="text-fg-muted">
          or press <kbd>⌘</kbd> <kbd>K</kbd> for the command palette
        </span>
      </div>
    </main>
  );
}
