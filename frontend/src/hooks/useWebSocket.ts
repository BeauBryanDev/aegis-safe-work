import { useEffect, useRef, useState } from "react"

export type SocketStatus = "idle" | "connecting" | "open" | "closed" | "error"

interface Options {
  /** Pass `enabled: false` to skip connecting (the backend isn't built yet). */
  enabled?: boolean
  onMessage?: (data: unknown) => void
  reconnectMs?: number
}

/**
 * Thin WebSocket wrapper for the future FastAPI backend (pushed PPE / fall
 * detections + alerts). Disabled by default until the backend exists — the
 * dashboard currently runs on mock telemetry (see useTelemetry).
 */
export const useWebSocket = (url: string, options: Options = {}) => {
  const { enabled = false, onMessage, reconnectMs = 3000 } = options
  const [status, setStatus] = useState<SocketStatus>("idle")
  const socketRef = useRef<WebSocket | null>(null)
  const onMessageRef = useRef(onMessage)
  onMessageRef.current = onMessage

  useEffect(() => {
    if (!enabled) return
    let retry: ReturnType<typeof setTimeout>
    let closedByUs = false

    const connect = () => {
      setStatus("connecting")
      const ws = new WebSocket(url)
      socketRef.current = ws

      ws.onopen = () => setStatus("open")
      ws.onerror = () => setStatus("error")
      ws.onmessage = (event) => {
        try {
          onMessageRef.current?.(JSON.parse(event.data))
        } catch {
          onMessageRef.current?.(event.data)
        }
      }
      ws.onclose = () => {
        setStatus("closed")
        if (!closedByUs) retry = setTimeout(connect, reconnectMs)
      }
    }

    connect()

    return () => {
      closedByUs = true
      clearTimeout(retry)
      socketRef.current?.close()
    }
  }, [url, enabled, reconnectMs])

  const send = (data: unknown) => {
    const ws = socketRef.current
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(typeof data === "string" ? data : JSON.stringify(data))
    }
  }

  return { status, send }
}
