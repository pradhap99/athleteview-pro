'use client';

import { useCallback, useMemo } from 'react';
import Link from 'next/link';
import type { Scene, ShootingDay, ProposedDiff } from '@throughline/shared';
import { useUiStore } from '@/lib/store';

/*
 * Stripboard (shooting schedule board).
 *
 * This is a static/optimistic UI demo with in-file mock data. In the real app
 * the board hydrates from the production graph:
 *   GET /v1/projects/{id}/graph  → { scenes, shootingDays, strips, ... }
 * loaded via TanStack Query, with edits applied optimistically and confirmed
 * against a ProposedDiff returned by the propagation engine.
 */

// --- Mock data ------------------------------------------------------------

const DAYS: ShootingDay[] = [
  { id: 'd1', index: 1, date: '2026-07-06', primaryLocation: 'Red Hook Warehouse' },
  { id: 'd2', index: 2, date: '2026-07-07', primaryLocation: 'Brooklyn Rooftop' },
  { id: 'd3', index: 3, date: '2026-07-08', primaryLocation: 'Prospect Park' },
];

/** Scenes grouped by shooting day id (mirrors strip ordering on the board). */
const SCENES_BY_DAY: Record<string, Scene[]> = {
  d1: [
    {
      id: 's1',
      number: '12',
      intExt: 'INT',
      location: 'Warehouse — Main Floor',
      timeOfDay: 'NIGHT',
      pageEighths: 12,
      heading: 'INT. WAREHOUSE - NIGHT',
      characters: ['MAYA', 'DET. COLE'],
    },
    {
      id: 's2',
      number: '12A',
      intExt: 'INT',
      location: 'Warehouse — Loading Dock',
      timeOfDay: 'NIGHT',
      pageEighths: 5,
      heading: 'INT. WAREHOUSE / LOADING DOCK - NIGHT',
      characters: ['MAYA'],
    },
  ],
  d2: [
    {
      id: 's3',
      number: '18',
      intExt: 'EXT',
      location: 'Rooftop',
      timeOfDay: 'DAY',
      pageEighths: 8,
      heading: 'EXT. ROOFTOP - DAY',
      characters: ['MAYA', 'RIVERA'],
    },
    {
      id: 's4',
      number: '19',
      intExt: 'INT/EXT',
      location: 'Stairwell → Rooftop',
      timeOfDay: 'DAY',
      pageEighths: 3,
      heading: 'INT/EXT. STAIRWELL - DAY',
      characters: ['RIVERA'],
    },
  ],
  d3: [
    {
      id: 's5',
      number: '24',
      intExt: 'EXT',
      location: 'Park — Boathouse',
      timeOfDay: 'DAY',
      pageEighths: 16,
      heading: 'EXT. PARK / BOATHOUSE - DAY',
      characters: ['MAYA', 'DET. COLE', 'RIVERA'],
    },
  ],
};

/** Mocked propagation result shown in the ripple panel. */
const RIPPLE: ProposedDiff = {
  id: 'diff-1',
  summary: '+1 cast hold day',
  dollarDelta: 8400,
  changes: [
    { path: 'shootingDays/d2/scenes', before: 1, after: 2 },
    { path: 'dood/RIVERA', before: 'W', after: 'H' },
  ],
};

// --- Presentation helpers -------------------------------------------------

function intExtColor(intExt: Scene['intExt']): string {
  if (intExt === 'EXT') return 'text-ext';
  if (intExt === 'INT/EXT') return 'text-day';
  return 'text-int';
}

function stripAccent(scene: Scene): string {
  // Day/night edge accent — classic stripboard color language.
  return scene.timeOfDay === 'NIGHT'
    ? 'border-l-[color:var(--night)]'
    : 'border-l-[color:var(--day)]';
}

function fmtEighths(pageEighths: number): string {
  const whole = Math.floor(pageEighths / 8);
  const rem = pageEighths % 8;
  if (whole && rem) return `${whole} ${rem}/8`;
  if (whole) return `${whole}`;
  return `${rem}/8`;
}

// --- Components ------------------------------------------------------------

function Strip({ scene }: { scene: Scene }) {
  const selectedSceneId = useUiStore((s) => s.selectedSceneId);
  const selectScene = useUiStore((s) => s.selectScene);
  const selected = selectedSceneId === scene.id;

  return (
    <button
      type="button"
      onClick={() => selectScene(scene.id)}
      aria-pressed={selected}
      className={[
        'flex w-full items-center gap-3 border-l-4 px-3 py-2 text-left',
        'rounded-r-[var(--radius)] border-y border-r border-border bg-surface',
        'transition-colors hover:bg-surface-2',
        selected ? 'ring-1 ring-accent' : '',
        stripAccent(scene),
      ].join(' ')}
    >
      <span className="w-10 font-mono text-fg-muted">{scene.number}</span>
      <span className={`w-16 font-mono text-xs ${intExtColor(scene.intExt)}`}>
        {scene.intExt}
      </span>
      <span className="flex-1 truncate text-fg">{scene.location}</span>
      <span className="hidden w-24 truncate text-xs text-fg-muted sm:block">
        {scene.characters.join(', ')}
      </span>
      <span className="w-14 text-right text-xs text-fg-muted">{scene.timeOfDay}</span>
      <span className="w-14 text-right font-mono text-xs text-fg-muted">
        {fmtEighths(scene.pageEighths)}
      </span>
    </button>
  );
}

function DayColumn({ day, scenes }: { day: ShootingDay; scenes: Scene[] }) {
  const eighths = scenes.reduce((sum, s) => sum + s.pageEighths, 0);
  return (
    <section className="min-w-0 flex-1">
      <div className="mb-2 flex items-baseline justify-between border-b border-border pb-1">
        <h2 className="text-sm font-semibold text-fg">
          Day {day.index}
          <span className="ml-2 font-normal text-fg-muted">{day.date}</span>
        </h2>
        <span className="text-xs text-fg-muted">{fmtEighths(eighths)} pgs</span>
      </div>
      <p className="mb-2 truncate text-xs text-fg-muted">{day.primaryLocation}</p>
      <div className="flex flex-col gap-1.5">
        {scenes.map((scene) => (
          <Strip key={scene.id} scene={scene} />
        ))}
      </div>
    </section>
  );
}

function RipplePanel({ diff }: { diff: ProposedDiff }) {
  const selectedSceneId = useUiStore((s) => s.selectedSceneId);
  const positive = diff.dollarDelta >= 0;
  const dollars = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(Math.abs(diff.dollarDelta));

  return (
    <aside className="w-72 shrink-0 rounded-[var(--radius)] border border-border bg-surface p-3">
      <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-fg-muted">
        Ripple preview
      </h3>
      <p className="mb-3 text-xs text-fg-muted">
        {selectedSceneId
          ? `Consequences of moving scene ${selectedSceneId}:`
          : 'Select a strip to preview consequences.'}
      </p>

      <div className="mb-3 rounded-md border border-border bg-surface-2 p-3">
        <div
          className={`text-lg font-semibold ${positive ? 'text-day' : 'text-ext'}`}
        >
          {positive ? '+' : '−'}
          {dollars} to the top sheet
        </div>
        <div className="text-sm text-fg-muted">· {diff.summary}</div>
      </div>

      <ul className="space-y-1 text-xs text-fg-muted">
        {diff.changes.map((c) => (
          <li key={c.path} className="font-mono">
            {c.path}: {String(c.before)} → {String(c.after)}
          </li>
        ))}
      </ul>

      <div className="mt-4 flex gap-2">
        <button
          type="button"
          className="flex-1 rounded-md bg-accent px-3 py-1.5 text-xs font-medium text-accent-fg hover:opacity-90"
          onClick={() => console.log('[board] confirm diff', diff.id)}
        >
          Confirm
        </button>
        <button
          type="button"
          className="rounded-md border border-border px-3 py-1.5 text-xs text-fg hover:bg-surface-2"
          onClick={() => console.log('[board] discard diff', diff.id)}
        >
          Discard
        </button>
      </div>
    </aside>
  );
}

// --- Page ------------------------------------------------------------------

export default function BoardPage() {
  const selectScene = useUiStore((s) => s.selectScene);

  // Flattened, day-ordered scene ids for keyboard navigation.
  const orderedSceneIds = useMemo(
    () => DAYS.flatMap((d) => (SCENES_BY_DAY[d.id] ?? []).map((s) => s.id)),
    [],
  );

  const move = useCallback(
    (dir: 1 | -1) => {
      const { selectedSceneId } = useUiStore.getState();
      if (orderedSceneIds.length === 0) return;
      const cur = selectedSceneId ? orderedSceneIds.indexOf(selectedSceneId) : -1;
      const next =
        cur === -1
          ? 0
          : (cur + dir + orderedSceneIds.length) % orderedSceneIds.length;
      selectScene(orderedSceneIds[next]);
    },
    [orderedSceneIds, selectScene],
  );

  const onKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'ArrowDown' || e.key === 'j') {
        e.preventDefault();
        move(1);
      } else if (e.key === 'ArrowUp' || e.key === 'k') {
        e.preventDefault();
        move(-1);
      } else if (e.key === 'Escape') {
        selectScene(null);
      }
    },
    [move, selectScene],
  );

  return (
    <main
      tabIndex={0}
      onKeyDown={onKeyDown}
      className="flex min-h-screen flex-col gap-4 px-6 py-5 focus:outline-none"
    >
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold tracking-tight text-fg">Stripboard</h1>
          <p className="text-xs text-fg-muted">
            <kbd>↑</kbd> <kbd>↓</kbd> / <kbd>j</kbd> <kbd>k</kbd> to navigate ·{' '}
            <kbd>⌘</kbd> <kbd>K</kbd> for commands
          </p>
        </div>
        <Link href="/" className="text-xs text-accent hover:underline">
          ← Dashboard
        </Link>
      </header>

      <div className="flex flex-1 gap-4">
        <div className="flex min-w-0 flex-1 gap-4">
          {DAYS.map((day) => (
            <DayColumn key={day.id} day={day} scenes={SCENES_BY_DAY[day.id] ?? []} />
          ))}
        </div>
        <RipplePanel diff={RIPPLE} />
      </div>
    </main>
  );
}
