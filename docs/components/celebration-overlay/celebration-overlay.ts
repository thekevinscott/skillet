import { LitElement, html, css } from 'lit'
import { state } from 'lit/decorators.js'
import { createConfetti } from '../../services/reactivity/celebration.js'

export const TAG_NAME = 'skillet-celebration-overlay'

interface CelebrationDetail {
  type: 'step-complete' | 'tutorial-complete' | 'achievement'
  message: string
  showConfetti?: boolean
  playSound?: boolean
  duration?: number
}

/**
 * Full-screen celebration overlay for major accomplishments.
 */
export class SkilletCelebrationOverlay extends LitElement {
  static styles = css`
    :host {
      display: block;
    }

    .overlay {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.5);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 9999;
      animation: fade-in 0.3s ease-out;
    }

    .celebration-card {
      background: var(--vp-c-bg, #fff);
      border-radius: 16px;
      padding: 48px;
      text-align: center;
      max-width: 400px;
      animation: scale-in 0.4s ease-out;
    }

    .celebration-icon {
      font-size: 72px;
      margin-bottom: 24px;
      animation: bounce 1s ease infinite;
    }

    .celebration-title {
      font-size: 28px;
      font-weight: 700;
      color: var(--vp-c-text-1, #111827);
      margin: 0 0 12px 0;
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .celebration-message {
      font-size: 16px;
      color: var(--vp-c-text-2, #6b7280);
      margin: 0 0 24px 0;
    }

    .celebration-button {
      background: var(--vp-c-brand-1, #8B7355);
      color: white;
      border: none;
      border-radius: 8px;
      padding: 12px 32px;
      font-size: 16px;
      font-weight: 500;
      cursor: pointer;
      transition: background-color 0.2s ease;
    }

    .celebration-button:hover {
      background: var(--vp-c-brand-3, #5C4D3D);
    }

    /* Step complete - subtle toast */
    .step-toast {
      position: fixed;
      top: 80px;
      left: 50%;
      transform: translateX(-50%);
      background: #10b981;
      color: white;
      padding: 12px 24px;
      border-radius: 8px;
      font-size: 14px;
      font-weight: 500;
      z-index: 1000;
      animation: slide-down 0.3s ease-out, slide-up 0.3s ease-in 1.7s forwards;
      box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    }

    @keyframes fade-in {
      from { opacity: 0; }
      to { opacity: 1; }
    }

    @keyframes scale-in {
      from {
        opacity: 0;
        transform: scale(0.8);
      }
      to {
        opacity: 1;
        transform: scale(1);
      }
    }

    @keyframes bounce {
      0%, 100% { transform: translateY(0); }
      50% { transform: translateY(-10px); }
    }

    @keyframes slide-down {
      from {
        opacity: 0;
        transform: translateX(-50%) translateY(-20px);
      }
      to {
        opacity: 1;
        transform: translateX(-50%) translateY(0);
      }
    }

    @keyframes slide-up {
      from {
        opacity: 1;
        transform: translateX(-50%) translateY(0);
      }
      to {
        opacity: 0;
        transform: translateX(-50%) translateY(-20px);
      }
    }
  `

  @state() private showOverlay = false
  @state() private showStepToast = false
  @state() private message = ''
  @state() private type: CelebrationDetail['type'] = 'step-complete'

  private boundHandleCelebration: (e: Event) => void

  constructor() {
    super()
    this.boundHandleCelebration = this.handleCelebration.bind(this)
  }

  connectedCallback() {
    super.connectedCallback()
    window.addEventListener('skillet-celebration', this.boundHandleCelebration)
  }

  disconnectedCallback() {
    super.disconnectedCallback()
    window.removeEventListener('skillet-celebration', this.boundHandleCelebration)
  }

  private handleCelebration(e: Event) {
    const detail = (e as CustomEvent<CelebrationDetail>).detail

    this.message = detail.message
    this.type = detail.type

    if (detail.type === 'step-complete') {
      // Show subtle toast for steps
      this.showStepToast = true
      setTimeout(() => {
        this.showStepToast = false
      }, 2000)
    } else {
      // Show full overlay for tutorial/achievement
      this.showOverlay = true

      if (detail.showConfetti) {
        createConfetti()
      }

      // Auto-hide after duration
      if (detail.duration) {
        setTimeout(() => {
          this.close()
        }, detail.duration)
      }
    }
  }

  private close() {
    this.showOverlay = false
  }

  private getIcon(): string {
    switch (this.type) {
      case 'step-complete':
        return '✓'
      case 'tutorial-complete':
        return '🎉'
      case 'achievement':
        return '🏆'
      default:
        return '⭐'
    }
  }

  render() {
    return html`
      ${this.showStepToast
        ? html`
            <div class="step-toast">
              <span>✓</span> ${this.message}
            </div>
          `
        : ''}

      ${this.showOverlay
        ? html`
            <div class="overlay" @click=${this.close}>
              <div class="celebration-card" @click=${(e: Event) => e.stopPropagation()}>
                <div class="celebration-icon">${this.getIcon()}</div>
                <h2 class="celebration-title">
                  ${this.type === 'tutorial-complete' ? 'Congratulations!' : 'Achievement Unlocked!'}
                </h2>
                <p class="celebration-message">${this.message}</p>
                <button class="celebration-button" @click=${this.close}>
                  Continue
                </button>
              </div>
            </div>
          `
        : ''}
    `
  }
}
