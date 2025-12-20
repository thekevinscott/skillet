/**
 * Progress celebration service for reactive docs.
 * Provides visual feedback when users complete steps or tutorials.
 */

import { docsEventBus } from '../event-bus.js'

export interface CelebrationOptions {
  /** Type of celebration */
  type: 'step-complete' | 'tutorial-complete' | 'achievement'
  /** Message to display */
  message?: string
  /** Duration in ms */
  duration?: number
  /** Whether to play confetti effect */
  confetti?: boolean
  /** Whether to play sound (if enabled) */
  sound?: boolean
}

export interface CelebrationEvent {
  type: CelebrationOptions['type']
  message: string
  timestamp: number
}

export class CelebrationService {
  private soundEnabled = false
  private confettiEnabled = true
  private celebrationHistory: CelebrationEvent[] = []

  constructor() {
    // Load preferences from localStorage
    if (typeof localStorage !== 'undefined') {
      this.soundEnabled = localStorage.getItem('skillet-celebration-sound') === 'true'
      this.confettiEnabled = localStorage.getItem('skillet-celebration-confetti') !== 'false'
    }
  }

  /** Enable/disable celebration sounds */
  setSoundEnabled(enabled: boolean): void {
    this.soundEnabled = enabled
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('skillet-celebration-sound', String(enabled))
    }
  }

  /** Enable/disable confetti effect */
  setConfettiEnabled(enabled: boolean): void {
    this.confettiEnabled = enabled
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('skillet-celebration-confetti', String(enabled))
    }
  }

  /** Celebrate a step completion */
  celebrateStep(stepIndex: number, stepTitle: string): void {
    this.celebrate({
      type: 'step-complete',
      message: `Step ${stepIndex + 1} complete!`,
      duration: 2000,
      confetti: false,
    })
  }

  /** Celebrate tutorial completion */
  celebrateTutorial(tutorialName: string): void {
    this.celebrate({
      type: 'tutorial-complete',
      message: `Congratulations! You completed "${tutorialName}"!`,
      duration: 5000,
      confetti: true,
      sound: true,
    })
  }

  /** Celebrate an achievement */
  celebrateAchievement(message: string): void {
    this.celebrate({
      type: 'achievement',
      message,
      duration: 4000,
      confetti: true,
      sound: true,
    })
  }

  /** Trigger a celebration */
  celebrate(options: CelebrationOptions): void {
    const event: CelebrationEvent = {
      type: options.type,
      message: options.message || this.getDefaultMessage(options.type),
      timestamp: Date.now(),
    }

    this.celebrationHistory.push(event)

    // Dispatch custom event for UI components to handle
    if (typeof window !== 'undefined') {
      window.dispatchEvent(
        new CustomEvent('skillet-celebration', {
          detail: {
            ...options,
            message: event.message,
            showConfetti: options.confetti && this.confettiEnabled,
            playSound: options.sound && this.soundEnabled,
          },
        })
      )
    }

    // Also emit via event bus
    docsEventBus.emit('step:complete', {
      index: -1,
      stepId: options.type,
    })
  }

  /** Get celebration history */
  getHistory(): CelebrationEvent[] {
    return [...this.celebrationHistory]
  }

  /** Clear celebration history */
  clearHistory(): void {
    this.celebrationHistory = []
  }

  private getDefaultMessage(type: CelebrationOptions['type']): string {
    switch (type) {
      case 'step-complete':
        return 'Step complete!'
      case 'tutorial-complete':
        return 'Tutorial complete!'
      case 'achievement':
        return 'Achievement unlocked!'
      default:
        return 'Great job!'
    }
  }
}

// Export singleton
export const celebrationService = new CelebrationService()

/**
 * Simple confetti effect using CSS animations.
 * Creates a burst of colorful particles.
 */
export function createConfetti(container?: HTMLElement): void {
  const target = container || document.body
  const colors = ['#8B7355', '#C4B5A5', '#10b981', '#f59e0b', '#3b82f6', '#ec4899']
  const particleCount = 50

  for (let i = 0; i < particleCount; i++) {
    const particle = document.createElement('div')
    particle.className = 'skillet-confetti-particle'
    particle.style.cssText = `
      position: fixed;
      width: 10px;
      height: 10px;
      background: ${colors[Math.floor(Math.random() * colors.length)]};
      left: ${Math.random() * 100}vw;
      top: -20px;
      border-radius: ${Math.random() > 0.5 ? '50%' : '2px'};
      transform: rotate(${Math.random() * 360}deg);
      animation: skillet-confetti-fall ${2 + Math.random() * 2}s ease-out forwards;
      animation-delay: ${Math.random() * 0.5}s;
      pointer-events: none;
      z-index: 9999;
    `
    target.appendChild(particle)

    // Clean up after animation
    setTimeout(() => {
      particle.remove()
    }, 4500)
  }

  // Inject animation if not already present
  if (!document.getElementById('skillet-confetti-styles')) {
    const style = document.createElement('style')
    style.id = 'skillet-confetti-styles'
    style.textContent = `
      @keyframes skillet-confetti-fall {
        0% {
          transform: translateY(0) rotate(0deg);
          opacity: 1;
        }
        100% {
          transform: translateY(100vh) rotate(720deg);
          opacity: 0;
        }
      }
    `
    document.head.appendChild(style)
  }
}
