import { LitElement, html, css } from 'lit'
import { property, state } from 'lit/decorators.js'

export const TAG_NAME = 'skillet-use-case-layout'

/**
 * Stripe-style two-column layout for use case walkthroughs.
 * Left: scrollable prose content
 * Right: sticky terminal/demo that updates per section
 */
export class SkilletUseCaseLayout extends LitElement {
  static styles = css`
    :host {
      display: block;
      --content-max-width: 1400px;
      --left-width: 50%;
      --right-width: 50%;
      --nav-height: 64px;
    }

    .layout {
      display: flex;
      max-width: var(--content-max-width);
      margin: 0 auto;
      min-height: calc(100vh - var(--nav-height));
    }

    /* Left column - scrollable content */
    .content {
      width: var(--left-width);
      padding: 48px 48px 120px 48px;
    }

    /* Right column - sticky terminal */
    .terminal-column {
      width: var(--right-width);
      position: relative;
    }

    .terminal-sticky {
      position: sticky;
      top: var(--nav-height);
      height: calc(100vh - var(--nav-height));
      padding: 24px;
      display: flex;
      flex-direction: column;
    }

    .terminal-wrapper {
      flex: 1;
      background: #0a0a0a;
      border-radius: 12px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      border: 1px solid #333;
    }

    .terminal-header {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 12px 16px;
      background: #1a1a1a;
      border-bottom: 1px solid #333;
    }

    .terminal-dot {
      width: 12px;
      height: 12px;
      border-radius: 50%;
    }
    .terminal-dot.red { background: #ff5f56; }
    .terminal-dot.yellow { background: #ffbd2e; }
    .terminal-dot.green { background: #27c93f; }

    .terminal-title {
      flex: 1;
      text-align: center;
      font-size: 13px;
      color: #666;
      font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .terminal-body {
      flex: 1;
      overflow: auto;
      padding: 16px;
      font-family: 'JetBrains Mono', 'Fira Code', monospace;
      font-size: 13px;
      line-height: 1.6;
      color: #e0e0e0;
    }

    /* Section indicator */
    .section-indicator {
      padding: 8px 16px;
      background: #1a1a1a;
      border-top: 1px solid #333;
      font-size: 12px;
      color: #888;
      font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .section-indicator .step {
      color: #4ade80;
      font-weight: 500;
    }

    /* Content styles */
    ::slotted(h1) {
      font-size: 2.5rem;
      font-weight: 700;
      margin: 0 0 16px 0;
      line-height: 1.2;
    }

    ::slotted(h2) {
      font-size: 1.5rem;
      font-weight: 600;
      margin: 48px 0 16px 0;
      padding-top: 24px;
      border-top: 1px solid #e5e5e5;
    }

    ::slotted(p) {
      margin: 0 0 16px 0;
      line-height: 1.7;
      color: #374151;
    }

    /* Responsive */
    @media (max-width: 900px) {
      .layout {
        flex-direction: column;
      }
      .content,
      .terminal-column {
        width: 100%;
      }
      .terminal-sticky {
        position: relative;
        top: 0;
        height: 400px;
      }
    }
  `

  @property({ type: String }) currentSection = ''
  @property({ type: String }) terminalContent = ''

  render() {
    return html`
      <div class="layout">
        <div class="content">
          <slot></slot>
        </div>
        <div class="terminal-column">
          <div class="terminal-sticky">
            <div class="terminal-wrapper">
              <div class="terminal-header">
                <span class="terminal-dot red"></span>
                <span class="terminal-dot yellow"></span>
                <span class="terminal-dot green"></span>
                <span class="terminal-title">Claude Code</span>
              </div>
              <div class="terminal-body">
                <slot name="terminal"></slot>
              </div>
              ${this.currentSection ? html`
                <div class="section-indicator">
                  <span class="step">${this.currentSection}</span>
                </div>
              ` : ''}
            </div>
          </div>
        </div>
      </div>
    `
  }
}
