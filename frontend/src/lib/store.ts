import { create } from "zustand";
import type { Citation } from "./api";

interface UIState {
  sidebarOpen: boolean;
  toggleSidebar: () => void;

  // 右侧来源面板
  sources: Citation[];
  sourcesOpen: boolean;
  setSources: (c: Citation[]) => void;
  openSources: () => void;
  closeSources: () => void;

  // 聊天会话状态 (sidebar 与 chat 页共享)
  personaId?: number;
  sessionId?: number;
  useAgent: boolean;
  newChatNonce: number;
  setPersona: (id?: number) => void;
  setSession: (id?: number) => void;
  setUseAgent: (v: boolean) => void;
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
  useAgent: false,
  newChatNonce: 0,
  setPersona: (id) => set({ personaId: id }),
  setSession: (id) => set({ sessionId: id }),
  setUseAgent: (v) => set({ useAgent: v }),
  newChat: () =>
    set((s) => ({ sessionId: undefined, sources: [], sourcesOpen: false, newChatNonce: s.newChatNonce + 1 })),
}));
