import { LitElement, html, css } from 'lit'
import { property, state } from 'lit/decorators.js'
import { docsEventBus } from '../../services/event-bus.js'
import type { Hint } from '../../services/reactivity/hints.js'

export const TAG_NAME = 'skillet-hint-toast'

/**
 * Toast notification component for displaying contextual hints.
 */
export class SkilletHintToast extends LitElement {
  static styles = css`
    :host {
      display: block;
      position: fixed;
      bottom: 24px;
      right: 24px;
      z-index: 1000;
      max-width: 400px;
    }

    .toast {
      background: var(--vp-c-bg, #fff);
      border: 1px solid var(--vp-c-border, #e5e7eb);
      border-radius: 8px;
      padding: 16px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
      animation: slide-in 0.3s ease-out;
      margin-top: 8px;
    }

    .toast.info {
      border-left: 4px solid #3b82f6;
    }

    .toast.warning {
      border-left: 4px solid #f59e0b;
    }

    .toast.error {
      border-left: 4px solid #ef4444;
    }

    .toast.success {
      border-left: 4px solid #10b981;
    }

    .toast-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 8px;
    }

    .toast-icon {
      font-size: 16px;
      margin-right: 8px;
    }

    .toast-message {
      font-size: 14px;
      font-weight: 500;
      color: var(--vp-c-text-1, #111827);
      flex: 1;
    }

    .toast-close {
      background: none;
      border: none;
      color: var(--vp-c-text-3, #9ca3af);
      cursor: pointer;
      padding: 4px;
      font-size: 16px;
      line-height: 1;
    }

    .toast-close:hover {
      color: var(--vp-c-text-1, #111827);
    }

    .toast-suggestion {
      font-size: 13px;
      color: var(--vp-c-text-2, #6b7280);
      margin-top: 4px;
    }

    .toast-action {
      margin-top: 12px;
    }

    .toast-action button {
      background: var(--vp-c-brand-1, #8B7355);
      color: white;
      border: none;
      border-radius: 4px;
      padding: 6px 12px;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      transition: background-color 0.2s ease;
    }

    .toast-action button:hover {
      background: var(--vp-c-brand-3, #5C4D3D);
    }

    @keyframes slide-in {
      from {
        transform: translateX(100%);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }

    @keyframes slide-out {
      from {
        transform: translateX(0);
        opacity: 1;
      }
      to {
        transform: translateX(100%);
        opacity: 0;
      }
    }

    .toast.hiding {
      animation: slide-out 0.2s ease-in forwards;
    }
  `

  @state() private hints: Hint[] = []

  private unsubscribers: Array<() => void> = []

  connectedCallback() {
    super.connectedCallback()

    // Listen for hint events
    this.unsubscribers.push(
      docsEventBus.on('hint:show', ({ message, type }) => {
        this.addHint({
          id: `toast-${Date.now()}`,
          message,
          type: type || 'info',
        })
      })
    )

    this.unsubscribers.push(
      docsEventBus.on('hint:hide', () => {
        // Remove last hint
        if (this.hints.length > 0) {
          this.removeHint(this.hints[this.hints.length - 1].id)
        }
      })
    )
  }

  disconnectedCallback() {
    super.disconnectedCallback()
    this.unsubscribers.forEach((unsub) => unsub())
    this.unsubscribers = []
  }

  private addHint(hint: Hint) {
    this.hints = [...this.hints, hint]

    // Auto-remove after timeout
    if (hint.timeout) {
      setTimeout(() => {
        this.removeHint(hint.id)
      }, hint.timeout)
    }
  }

  private removeHint(id: string) {
    this.hints = this.hints.filter((h) => h.id !== id)
  }

  private handleAction(hint: Hint) {
    if (hint.action) {
      docsEventBus.emit('docs:execute', hint.action.command)
      this.removeHint(hint.id)
    }
  }

  private getIcon(type: Hint['type']): string {
    switch (type) {
      case 'info':
        return 'ℹ️'
      case 'warning':
        return '⚠️'
      case 'error':
        return '❌'
      case 'success':
        return '✅'
      default:
        return '💡'
    }
  }

  render() {
    return html`
      ${this.hints.map(
        (hint) => html`
          <div class="toast ${hint.type}">
            <div class="toast-header">
              <span class="toast-icon">${this.getIcon(hint.type)}</span>
              <span class="toast-message">${hint.message}</span>
              <button
                class="toast-close"
                @click=${() => this.removeHint(hint.id)}
              >
                ×
              </button>
            </div>
            ${hint.suggestion
              ? html`<div class="toast-suggestion">${hint.suggestion}</div>`
              : ''}
            ${hint.action
              ? html`
                  <div class="toast-action">
                    <button @click=${() => this.handleAction(hint)}>
                      ${hint.action.label}
                    </button>
                  </div>
                `
              : ''}
          </div>
        `
      )}
    `
  }
}
