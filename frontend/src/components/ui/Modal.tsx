import { ReactNode } from "react"
import { X } from "lucide-react"

interface ModalProps {
  open: boolean
  title?: string
  onClose: () => void
  children: ReactNode
}

const Modal = ({ open, title, onClose, children }: ModalProps) => {
  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-lg rounded-md border border-cyber-orange/50 bg-gradient-to-br from-cyber-orange/10 to-black p-4 shadow-[0_0_20px_rgba(255,106,0,0.5)]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-3 flex items-center justify-between border-b border-cyber-orange/30 pb-2">
          <h2 className="text-sm uppercase tracking-[0.18em] text-cyber-orange text-glow">
            {title}
          </h2>
          <button
            onClick={onClose}
            aria-label="Close"
            className="text-cyber-orange/70 transition-colors hover:text-cyber-orange"
          >
            <X size={18} />
          </button>
        </div>
        {children}
      </div>
    </div>
  )
}

export default Modal
