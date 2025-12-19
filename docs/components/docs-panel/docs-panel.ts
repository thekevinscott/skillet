import { LitElement, html, unsafeCSS } from 'lit'
import { property } from 'lit/decorators.js'
import type { TutorialState, TutorialStep } from '../../services/tutorial-types.js'
import styles from './docs-panel.css?raw'

export const TAG_NAME = 'skillet-docs-panel'

/**
 * Documentation panel that displays tutorial steps and [Show me] buttons.
 */
export class SkilletDocsPanel extends LitElement {
  static styles = unsafeCSS(styles)

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
