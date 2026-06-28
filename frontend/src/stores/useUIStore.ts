import { create } from "zustand"

interface UIState {
  /** desktop sidebar collapsed to icons only */
  sidebarCollapsed: boolean
  /** mobile slide-over menu open */
  mobileMenuOpen: boolean
  /** generic modal slot */
  activeModal: string | null

  toggleSidebar: () => void
  setMobileMenu: (open: boolean) => void
  openModal: (id: string) => void
  closeModal: () => void
}

export const useUIStore = create<UIState>((set) => ({
  sidebarCollapsed: false,
  mobileMenuOpen: false,
  activeModal: null,

  toggleSidebar: () =>
    set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
  setMobileMenu: (open) => set({ mobileMenuOpen: open }),
  openModal: (id) => set({ activeModal: id }),
  closeModal: () => set({ activeModal: null }),
}))
