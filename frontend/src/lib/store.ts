import { create } from "zustand";
import type { Citation } from "./api";

interface UIState {
  sidebarOpen: boolean;
  toggleSidebar: () => void;

  sources: Citation[];
  sourcesOpen: boolean;
  setSources: (c: Citation[]) => void;
  openSources: () => void;
  closeSources: () => void;

  personaId?: number;
  sessionId?: number;
  newChatNonce: number;
  setPersona: (id?: number) => void;
  setSession: (id?: number) => void;
  newChat: () => void;
}

export const useUI = create<UIState>((set) => ({
  sidebarOpen: true,
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),

  sources: [],
  sourcesOpen: false,
  setSources: (c) => set({ sources: c, sourcesOpen: c.length > 0 }),
  openSources: () => set({ sourcesOpen: true }),
  closeSources: () => set({ sourcesOpen: false }),

  personaId: undefined,
  sessionId: undefined,
  newChatNonce: 0,
  setPersona: (id) => set({ personaId: id }),
  setSession: (id) => set({ sessionId: id }),
  newChat: () =>
    set((s) => ({ sessionId: undefined, sources: [], sourcesOpen: false, newChatNonce: s.newChatNonce + 1 })),
}));
