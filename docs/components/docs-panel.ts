import { LitElement, html, css } from 'lit'
import { customElement, property } from 'lit/decorators.js'
import type { TutorialState, TutorialStep } from '../services/tutorial-types'

/**
 * Documentation panel that displays tutorial steps and [Show me] buttons.
 */
@customElement('skillet-docs-panel')
export class SkilletDocsPanel extends LitElement {
  static styles = css`
    :host {
      display: block;
      height: 100%;
    }

    .container {
      height: 100%;
      display: flex;
      flex-direction: column;
      padding: 24px;
      background: #fafafa;
      overflow-y: auto;
      box-sizing: border-box;
    }

    .progress {
      margin-bottom: 24px;
    }

    .progress-text {
      font-size: 13px;
      color: #6b7280;
      margin-bottom: 8px;
    }

    .progress-bar {
      height: 4px;
      background: #e5e7eb;
      border-radius: 2px;
      overflow: hidden;
    }

    .progress-fill {
      height: 100%;
      background: #8B7355;
      transition: width 0.3s ease;
    }

    .step {
      flex: 1;
    }

    .step-title {
      font-size: 24px;
      font-weight: 600;
      color: #111827;
      margin: 0 0 12px 0;
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }

    .step-description {
      font-size: 16px;
      line-height: 1.6;
      color: #374151;
      margin-bottom: 20px;
    }

    .command-preview {
      background: #1a1a1a;
      padding: 12px 16px;
      border-radius: 8px;
      margin-bottom: 20px;
    }

    .command-code {
      font-family: Menlo, Monaco, 'Courier New', monospace;
      font-size: 14px;
      color: #d4d4d4;
    }

    .actions {
      display: flex;
      gap: 12px;
      align-items: center;
      margin-bottom: 20px;
    }

    .show-me-button {
      padding: 12px 24px;
      background: #8B7355;
      color: white;
      border: none;
      border-radius: 8px;
      font-size: 16px;
      font-weight: 500;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .show-me-button:disabled {
      opacity: 0.7;
      cursor: not-allowed;
    }

    .skip-button {
      padding: 12px 20px;
      background: transparent;
      color: #6b7280;
      border: 1px solid #d1d5db;
      border-radius: 8px;
      font-size: 14px;
      cursor: pointer;
    }

    .skip-button:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .waiting-message {
      padding: 12px 16px;
      background: #fef3c7;
      color: #92400e;
      border-radius: 8px;
      font-size: 14px;
    }

    .hint {
      padding: 12px 16px;
      background: #eff6ff;
      border-radius: 8px;
      font-size: 14px;
      color: #1e40af;
    }

    .hint-label {
      font-weight: 600;
    }

    .step-list {
      margin-top: auto;
      padding-top: 24px;
      border-top: 1px solid #e5e7eb;
    }

    .step-indicator {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 8px 0;
    }

    .step-dot {
      width: 20px;
      height: 20px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: 10px;
      flex-shrink: 0;
    }

    .step-label {
      font-size: 14px;
      color: #374151;
    }

    .complete {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100%;
      text-align: center;
    }

    .complete-icon {
      width: 64px;
      height: 64px;
      border-radius: 50%;
      background: #10b981;
      color: white;
      font-size: 32px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 24px;
    }

    .complete-title {
      font-size: 28px;
      font-weight: 600;
      color: #111827;
      margin: 0 0 12px 0;
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }

    .complete-text {
      font-size: 16px;
      color: #6b7280;
      margin-bottom: 24px;
    }

    .reset-button {
      padding: 12px 24px;
      background: #8B7355;
      color: white;
      border: none;
      border-radius: 8px;
      font-size: 16px;
      font-weight: 500;
      cursor: pointer;
    }
  `

  @property({ type: Object }) state!: TutorialState
  @property({ type: Boolean }) isExecuting = false

  private handleShowMe() {
    this.dispatchEvent(new CustomEvent('show-me'))
  }

  private handleSkip() {
    this.dispatchEvent(new CustomEvent('skip'))
  }

  private handleReset() {
    this.dispatchEvent(new CustomEvent('reset'))
  }

  render() {
    const { tutorial, currentStepIndex, isComplete } = this.state
    const currentStep = tutorial.steps[currentStepIndex]

    if (isComplete) {
      return html`
        <div class="container">
          <div class="complete">
            <div class="complete-icon">✓</div>
            <h2 class="complete-title">Tutorial Complete!</h2>
            <p class="complete-text">You've completed the ${tutorial.name} tutorial.</p>
            <button class="reset-button" @click=${this.handleReset}>Start Over</button>
          </div>
        </div>
      `
    }

    return html`
      <div class="container">
        <!-- Progress indicator -->
        <div class="progress">
          <div class="progress-text">Step ${currentStepIndex + 1} of ${tutorial.steps.length}</div>
          <div class="progress-bar">
            <div
              class="progress-fill"
              style="width: ${((currentStepIndex + 1) / tutorial.steps.length) * 100}%"
            ></div>
          </div>
        </div>

        <!-- Current step -->
        <div class="step">
          <h2 class="step-title">${currentStep.title}</h2>
          <p class="step-description">${currentStep.description}</p>

          ${currentStep.command && !currentStep.requiresUserAction ? html`
            <div class="command-preview">
              <code class="command-code">${currentStep.command}</code>
            </div>
          ` : ''}

          <div class="actions">
            ${!currentStep.requiresUserAction && currentStep.command ? html`
              <button
                class="show-me-button"
                ?disabled=${this.isExecuting}
                @click=${this.handleShowMe}
              >
                ${this.isExecuting
                  ? currentStep.runningLabel || 'Running...'
                  : currentStep.showMeLabel || 'Show me'}
              </button>
            ` : ''}

            ${currentStep.requiresUserAction ? html`
              <div class="waiting-message">
                Waiting for you to complete this step in the terminal...
              </div>
            ` : ''}

            <button
              class="skip-button"
              ?disabled=${this.isExecuting}
              @click=${this.handleSkip}
            >Skip</button>
          </div>

          ${currentStep.hint ? html`
            <div class="hint">
              <span class="hint-label">Hint:</span> ${currentStep.hint}
            </div>
          ` : ''}
        </div>

        <!-- Step list -->
        <div class="step-list">
          ${tutorial.steps.map((step, index) => this.renderStepIndicator(step, index, currentStepIndex))}
        </div>
      </div>
    `
  }

  private renderStepIndicator(step: TutorialStep, index: number, currentIndex: number) {
    const isComplete = index < currentIndex
    const isCurrent = index === currentIndex

    return html`
      <div class="step-indicator" style="opacity: ${isComplete || isCurrent ? 1 : 0.5}">
        <div
          class="step-dot"
          style="background: ${isComplete ? '#10b981' : isCurrent ? '#8B7355' : '#d1d5db'}"
        >
          ${isComplete ? '✓' : ''}
        </div>
        <span class="step-label" style="font-weight: ${isCurrent ? 600 : 400}">
          ${step.title}
        </span>
      </div>
    `
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'skillet-docs-panel': SkilletDocsPanel
  }
}
