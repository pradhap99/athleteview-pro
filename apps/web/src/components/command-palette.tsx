'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Command } from 'cmdk';
import { useUiStore } from '@/lib/store';

interface Action {
  id: string;
  label: string;
  hint?: string;
  run: (router: ReturnType<typeof useRouter>) => void;
}

/**
 * Graph actions. In the real app these dispatch through the API layer
 * (writes route through /v1/... for authz + event-log append) and surface a
 * ProposedDiff for the user to confirm. Here they are stubs.
 */
const ACTIONS: Action[] = [
  {
    id: 'import-script',
    label: 'Import script',
    hint: 'FDX / PDF',
    run: () => console.log('[palette] import script → open uploader'),
  },
  {
    id: 'optimize-schedule',
    label: 'Optimize schedule',
    hint: 'CP-SAT',
    run: () => console.log('[palette] optimize schedule → propose diff'),
  },
  {
    id: 'export-budget',
    label: 'Export AICP budget',
    run: () => console.log('[palette] export AICP budget'),
  },
  {
    id: 'go-stripboard',
    label: 'Go to stripboard',
    run: (router) => router.push('/board'),
  },
  {
    id: 'search-production',
    label: 'Search production',
    hint: 'scenes, elements, cast',
    run: () => console.log('[palette] search production'),
  },
];

export function CommandPalette() {
  const router = useRouter();
  const open = useUiStore((s) => s.paletteOpen);
  const setOpen = useUiStore((s) => s.setPaletteOpen);
  const toggle = useUiStore((s) => s.togglePalette);

  // Open on Cmd/Ctrl+K.
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key.toLowerCase() === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        toggle();
      }
    };
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [toggle]);

  return (
    <Command.Dialog
      open={open}
      onOpenChange={setOpen}
      label="Command palette"
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/50 pt-[18vh]"
    >
      <div className="w-full max-w-xl overflow-hidden rounded-lg border border-border bg-surface shadow-2xl">
        <Command.Input
          autoFocus
          placeholder="Type a command or search…"
          className="w-full border-b border-border bg-transparent px-4 py-3 text-sm text-fg placeholder:text-fg-muted focus:outline-none"
        />
        <Command.List className="max-h-80 overflow-y-auto p-2">
          <Command.Empty className="px-2 py-6 text-center text-fg-muted">
            No results.
          </Command.Empty>
          <Command.Group
            heading="Graph actions"
            className="px-2 pb-1 pt-2 text-[11px] uppercase tracking-wide text-fg-muted"
          >
            {ACTIONS.map((action) => (
              <Command.Item
                key={action.id}
                value={action.label}
                onSelect={() => {
                  action.run(router);
                  setOpen(false);
                }}
                className="flex cursor-pointer items-center justify-between rounded-md px-2 py-2 text-sm text-fg data-[selected=true]:bg-surface-2"
              >
                <span>{action.label}</span>
                {action.hint ? (
                  <span className="text-[11px] text-fg-muted">{action.hint}</span>
                ) : null}
              </Command.Item>
            ))}
          </Command.Group>
        </Command.List>
      </div>
    </Command.Dialog>
  );
}
