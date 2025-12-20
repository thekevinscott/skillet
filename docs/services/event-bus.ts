/**
 * Simple event bus for reactive docs communication.
 * Enables decoupled communication between terminal and docs components.
 */

type EventCallback<T = unknown> = (data: T) => void
type UnsubscribeFn = () => void

export interface DocsEventMap {
  // Terminal → Docs events
  'terminal:ready': void
  'terminal:output': string
  'terminal:command': string
  'terminal:error': string

  // Docs → Terminal events
  'docs:execute': string
  'docs:type': { text: string; delay?: number }

  // Step navigation events
  'step:change': { index: number; stepId: string }
  'step:complete': { index: number; stepId: string }
  'step:visible': { index: number; stepId: string; ratio: number }

  // Reactivity events
  'hint:show': { message: string; type?: 'info' | 'warning' | 'error' }
  'hint:hide': void
  'pattern:match': { stepId: string; pattern: string }
  'error:detected': { message: string; suggestion?: string }
}

class EventBus {
  private listeners = new Map<string, Set<EventCallback>>()

  on<K extends keyof DocsEventMap>(
    event: K,
    callback: EventCallback<DocsEventMap[K]>
  ): UnsubscribeFn {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set())
    }
    this.listeners.get(event)!.add(callback as EventCallback)

    return () => {
      this.listeners.get(event)?.delete(callback as EventCallback)
    }
  }

  once<K extends keyof DocsEventMap>(
    event: K,
    callback: EventCallback<DocsEventMap[K]>
  ): UnsubscribeFn {
    const unsubscribe = this.on(event, (data) => {
      unsubscribe()
      callback(data)
    })
    return unsubscribe
  }

  emit<K extends keyof DocsEventMap>(event: K, data: DocsEventMap[K]): void {
    const callbacks = this.listeners.get(event)
    if (callbacks) {
      callbacks.forEach((callback) => callback(data))
    }
  }

  off<K extends keyof DocsEventMap>(
    event: K,
    callback?: EventCallback<DocsEventMap[K]>
  ): void {
    if (callback) {
      this.listeners.get(event)?.delete(callback as EventCallback)
    } else {
      this.listeners.delete(event)
    }
  }

  clear(): void {
    this.listeners.clear()
  }
}

// Singleton instance for global communication
export const docsEventBus = new EventBus()

// Export class for testing or isolated instances
export { EventBus }
