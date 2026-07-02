import { create } from 'zustand';
import type { Id } from '@throughline/shared';

/**
 * UI-only state (Zustand). Server/graph state lives in TanStack Query — do not
 * cache API entities here. Keep this store small and synchronous so reads are
 * cheap and interactions stay well under the <100ms budget.
 */
interface UiState {
  /** Currently selected scene strip on the board, if any. */
  selectedSceneId: Id | null;
  /** Whether the ⌘K command palette is open. */
  paletteOpen: boolean;

  selectScene: (id: Id | null) => void;
  setPaletteOpen: (open: boolean) => void;
  togglePalette: () => void;
}

export const useUiStore = create<UiState>((set) => ({
  selectedSceneId: null,
  paletteOpen: false,

  selectScene: (id) => set({ selectedSceneId: id }),
  setPaletteOpen: (open) => set({ paletteOpen: open }),
  togglePalette: () => set((s) => ({ paletteOpen: !s.paletteOpen })),
}));
