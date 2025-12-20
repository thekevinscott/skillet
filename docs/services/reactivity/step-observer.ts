/**
 * Intersection Observer wrapper for tracking step visibility.
 * Used to detect which step is currently in view during scrolling.
 */

import { docsEventBus } from '../event-bus.js'

export interface StepVisibility {
  index: number
  stepId: string
  ratio: number
  isIntersecting: boolean
}

export interface StepObserverOptions {
  /** Root element for intersection (null = viewport) */
  root?: Element | null
  /** Margin around root */
  rootMargin?: string
  /** Visibility thresholds to trigger callbacks */
  threshold?: number | number[]
  /** Emit events to the event bus */
  emitEvents?: boolean
}

export class StepObserver {
  private observer: IntersectionObserver | null = null
  private stepElements = new Map<Element, { index: number; stepId: string }>()
  private visibleSteps = new Map<string, StepVisibility>()
  private onChangeCallback?: (visible: StepVisibility[]) => void
  private options: StepObserverOptions

  constructor(options: StepObserverOptions = {}) {
    this.options = {
      root: null,
      rootMargin: '0px',
      threshold: [0, 0.25, 0.5, 0.75, 1],
      emitEvents: true,
      ...options,
    }
  }

  /** Initialize the observer */
  init(): void {
    if (typeof IntersectionObserver === 'undefined') {
      console.warn('IntersectionObserver not supported')
      return
    }

    this.observer = new IntersectionObserver(
      (entries) => this.handleIntersection(entries),
      {
        root: this.options.root,
        rootMargin: this.options.rootMargin,
        threshold: this.options.threshold,
      }
    )
  }

  /** Set callback for visibility changes */
  onChange(callback: (visible: StepVisibility[]) => void): void {
    this.onChangeCallback = callback
  }

  /** Observe a step element */
  observe(element: Element, index: number, stepId: string): void {
    if (!this.observer) {
      this.init()
    }

    this.stepElements.set(element, { index, stepId })
    this.observer?.observe(element)
  }

  /** Stop observing a step element */
  unobserve(element: Element): void {
    const stepInfo = this.stepElements.get(element)
    if (stepInfo) {
      this.visibleSteps.delete(stepInfo.stepId)
      this.stepElements.delete(element)
    }
    this.observer?.unobserve(element)
  }

  /** Get the most visible step */
  getMostVisible(): StepVisibility | null {
    if (this.visibleSteps.size === 0) return null

    let mostVisible: StepVisibility | null = null
    for (const visibility of this.visibleSteps.values()) {
      if (!mostVisible || visibility.ratio > mostVisible.ratio) {
        mostVisible = visibility
      }
    }
    return mostVisible
  }

  /** Get all visible steps sorted by visibility ratio */
  getVisibleSteps(): StepVisibility[] {
    return Array.from(this.visibleSteps.values()).sort(
      (a, b) => b.ratio - a.ratio
    )
  }

  /** Clean up */
  destroy(): void {
    this.observer?.disconnect()
    this.observer = null
    this.stepElements.clear()
    this.visibleSteps.clear()
  }

  private handleIntersection(entries: IntersectionObserverEntry[]): void {
    let changed = false

    for (const entry of entries) {
      const stepInfo = this.stepElements.get(entry.target)
      if (!stepInfo) continue

      const visibility: StepVisibility = {
        index: stepInfo.index,
        stepId: stepInfo.stepId,
        ratio: entry.intersectionRatio,
        isIntersecting: entry.isIntersecting,
      }

      if (entry.isIntersecting) {
        this.visibleSteps.set(stepInfo.stepId, visibility)
        changed = true

        if (this.options.emitEvents) {
          docsEventBus.emit('step:visible', {
            index: stepInfo.index,
            stepId: stepInfo.stepId,
            ratio: entry.intersectionRatio,
          })
        }
      } else {
        if (this.visibleSteps.has(stepInfo.stepId)) {
          this.visibleSteps.delete(stepInfo.stepId)
          changed = true
        }
      }
    }

    if (changed) {
      this.onChangeCallback?.(this.getVisibleSteps())
    }
  }
}

// Export singleton for shared use
export const stepObserver = new StepObserver()
