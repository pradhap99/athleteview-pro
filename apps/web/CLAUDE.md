# apps/web — Throughline frontend

The Next.js frontend for Throughline: the "living production graph" UI
(stripboard, breakdown review, budget views).

## Stack
- **Next.js 15** (App Router) + **React 19** + **TypeScript** (strict).
- **TanStack Query** — server/graph state (never cache API entities in Zustand).
- **Zustand** — UI-only state (selection, palette open); see `src/lib/store.ts`.
- **shadcn/ui-style** components + **Tailwind CSS v4** (`@import "tailwindcss"`,
  no `tailwind.config.js`; theme tokens live in `src/app/globals.css`).
- **TanStack Virtual** — virtualize big boards/DOOD grids (add when a view needs it).
- **cmdk** — the ⌘K command palette (`src/components/command-palette.tsx`).

## Principles
- **Local-first + optimistic:** render from local/cached state immediately; apply
  edits optimistically and reconcile against the API. Never block render on a fetch.
- **Keyboard-first:** every core action reachable from the keyboard / ⌘K.
- **Interaction budget < 100ms** (target 50–60ms) for any keystroke or selection.
- **Human confirms:** AI outputs are DRAFTS. Every graph edit surfaces a reviewable
  `ProposedDiff` (dollar delta + summary) that a human confirms; writes route
  through the API for authz + event-log append.

## Types
- All domain types come from **`@throughline/shared`**, which is **generated from
  `docs/openapi.yaml`**. **Never hand-edit generated types** — regenerate from the
  OpenAPI contract instead.
- API surface: `/v1/...` (kebab-case URLs, camelCase JSON, cursor pagination).
  The stripboard would hydrate from `GET /v1/projects/{id}/graph`.

## Commands
- `pnpm --filter @throughline/web dev` — dev server
- `pnpm --filter @throughline/web typecheck` — `tsc --noEmit`
- `pnpm --filter @throughline/web lint` — `next lint`

## Layout
- `src/app/` — App Router: `layout.tsx` (Providers), `page.tsx` (dashboard),
  `board/page.tsx` (stripboard).
- `src/app/providers.tsx` — `"use client"`: QueryClientProvider + CommandPalette.
- `src/components/` — reusable UI (command palette, future shadcn-style primitives).
- `src/lib/` — client utilities and the Zustand store.
