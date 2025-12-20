import { LitElement, html, unsafeCSS, css, nothing } from 'lit'
import { property, state, query } from 'lit/decorators.js'
import type { TutorialState, TutorialStep } from '../../services/tutorial-types.js'
import { StepObserver } from '../../services/reactivity/step-observer.js'
import { docsEventBus } from '../../services/event-bus.js'
import styles from './docs-panel.css?raw'

export const TAG_NAME = 'skillet-docs-panel'

export type LayoutMode = 'single' | 'scroll-snap'

/**
 * Documentation panel that displays tutorial steps.
 * Supports two modes:
 * - 'single': Shows one step at a time (original behavior)
 * - 'scroll-snap': Shows all steps as scrollable cards with snap points
 */
export class SkilletDocsPanel extends LitElement {
  static styles = [
    unsafeCSS(styles),
    css`
      /* Scroll-snap mode styles */
      .scroll-container {
        height: 100%;
        overflow-y: scroll;
        scroll-snap-type: y mandatory;
        scroll-behavior: smooth;
        scrollbar-width: thin;
        scrollbar-color: var(--vp-c-border, #d1d5db) transparent;
      }

      .scroll-container::-webkit-scrollbar {
        width: 6px;
      }

      .scroll-container::-webkit-scrollbar-track {
        background: transparent;
      }

      .scroll-container::-webkit-scrollbar-thumb {
        background: var(--vp-c-border, #d1d5db);
        border-radius: 3px;
      }

      .step-card {
        scroll-snap-align: start;
        min-height: 100%;
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
        padding: 24px;
        border-bottom: 1px solid var(--vp-c-border, #e5e7eb);
      }

      .step-card:last-child {
        border-bottom: none;
      }

      .step-card.active {
        background: rgba(139, 115, 85, 0.04);
      }

      .step-card.completed {
        opacity: 0.7;
      }

      .step-number {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 12px;
      }

      .step-number.pending {
        background: var(--vp-c-border, #d1d5db);
        color: var(--vp-c-text-2, #6b7280);
      }

      .step-number.active {
        background: var(--vp-c-brand-1, #8B7355);
        color: white;
      }

      .step-number.completed {
        background: #10b981;
        color: white;
      }

      /* Progress dots for scroll mode */
      .scroll-progress {
        position: sticky;
        top: 0;
        z-index: 10;
        display: flex;
        gap: 8px;
        padding: 12px 24px;
        background: var(--vp-c-bg-soft, #fafafa);
        border-bottom: 1px solid var(--vp-c-border, #e5e7eb);
      }

      .progress-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--vp-c-border, #d1d5db);
        transition: all 0.2s ease;
        cursor: pointer;
      }

      .progress-dot.active {
        background: var(--vp-c-brand-1, #8B7355);
        transform: scale(1.25);
      }

      .progress-dot.completed {
        background: #10b981;
      }
    `,
  ]

  @property({ type: Object }) state!: TutorialState
  @property({ type: Boolean }) isExecuting = false
  @property({ type: String }) mode: LayoutMode = 'single'

  @state() private visibleStepIndex = 0

  @query('.scroll-container') private scrollContainer?: HTMLElement

  private stepObserver: StepObserver | null = null
  private stepElements: HTMLElement[] = []

  connectedCallback() {
    super.connectedCallback()
    if (this.mode === 'scroll-snap') {
      this.setupStepObserver()
    }
  }

  disconnectedCallback() {
    super.disconnectedCallback()
    this.stepObserver?.destroy()
    this.stepObserver = null
  }

  updated(changedProps: Map<string, unknown>) {
    if (changedProps.has('mode') && this.mode === 'scroll-snap') {
      this.setupStepObserver()
      // Re-observe elements after render
      this.updateComplete.then(() => this.observeStepElements())
    }
  }

  private setupStepObserver() {
    this.stepObserver?.destroy()
    this.stepObserver = new StepObserver({
      root: this.scrollContainer || null,
      rootMargin: '-10% 0px -70% 0px', // Consider step visible when in top 20-30%
      threshold: [0, 0.5, 1],
      emitEvents: true,
    })
    this.stepObserver.init()
    this.stepObserver.onChange((visible) => {
      if (visible.length > 0) {
        this.visibleStepIndex = visible[0].index
      }
    })
  }

  private observeStepElements() {
    if (!this.stepObserver) return

    const container = this.shadowRoot?.querySelector('.scroll-container')
    if (!container) return

    const cards = container.querySelectorAll('.step-card')
    cards.forEach((card, index) => {
      const step = this.state.tutorial.steps[index]
      if (step) {
        this.stepObserver!.observe(card, index, step.id)
      }
    })
  }

  private handleShowMe(stepIndex: number) {
    this.dispatchEvent(
      new CustomEvent('show-me', {
        detail: { stepIndex },
      })
    )
  }

  private handleSkip(stepIndex: number) {
    this.dispatchEvent(
      new CustomEvent('skip', {
        detail: { stepIndex },
      })
    )
  }

  private handleReset() {
    this.dispatchEvent(new CustomEvent('reset'))
  }

  private scrollToStep(index: number) {
    const container = this.shadowRoot?.querySelector('.scroll-container')
    const cards = container?.querySelectorAll('.step-card')
    if (cards && cards[index]) {
      cards[index].scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  private handleDotClick(index: number) {
    this.scrollToStep(index)
  }

  render() {
    if (this.mode === 'scroll-snap') {
      return this.renderScrollSnapMode()
    }
    return this.renderSingleMode()
  }

  private renderScrollSnapMode() {
    const { tutorial, currentStepIndex, isComplete } = this.state

    return html`
      <div class="container">
        <!-- Progress dots -->
        <div class="scroll-progress">
          ${tutorial.steps.map((_, index) => {
            const isCompleted = index < currentStepIndex
            const isActive = index === this.visibleStepIndex
            return html`
              <div
                class="progress-dot ${isCompleted ? 'completed' : ''} ${isActive ? 'active' : ''}"
                @click=${() => this.handleDotClick(index)}
                title="Step ${index + 1}: ${tutorial.steps[index].title}"
              ></div>
            `
          })}
        </div>

        <!-- Scrollable step cards -->
        <div class="scroll-container">
          ${tutorial.steps.map((step, index) =>
            this.renderStepCard(step, index, currentStepIndex)
          )}
          ${isComplete ? this.renderCompleteCard() : nothing}
        </div>
      </div>
    `
  }

  private renderStepCard(
    step: TutorialStep,
    index: number,
    currentStepIndex: number
  ) {
    const isCompleted = index < currentStepIndex
    const isActive = index === currentStepIndex
    const isPending = index > currentStepIndex

    const getStatus = () => {
      if (isCompleted) return 'completed'
      if (isActive) return 'active'
      return 'pending'
    }

    return html`
      <div
        class="step-card ${getStatus()}"
        data-step-id=${step.id}
        data-step-index=${index}
      >
        <div class="step-number ${getStatus()}">
          ${isCompleted ? '✓' : index + 1}
        </div>

        <h2 class="step-title">${step.title}</h2>
        <p class="step-description">${step.description}</p>

        ${step.command && !step.requiresUserAction
          ? html`
              <div class="command-preview">
                <code class="command-code">${step.command}</code>
              </div>
            `
          : nothing}

        <div class="actions">
          ${!step.requiresUserAction && step.command && !isCompleted
            ? html`
                <button
                  class="show-me-button"
                  ?disabled=${this.isExecuting || isPending}
                  @click=${() => this.handleShowMe(index)}
                >
                  ${this.isExecuting && isActive
                    ? step.runningLabel || 'Running...'
                    : step.showMeLabel || 'Show me'}
                </button>
              `
            : nothing}
          ${step.requiresUserAction && isActive
            ? html`
                <div class="waiting-message">
                  Waiting for you to complete this step in the terminal...
                </div>
              `
            : nothing}
          ${isActive && !isCompleted
            ? html`
                <button
                  class="skip-button"
                  ?disabled=${this.isExecuting}
                  @click=${() => this.handleSkip(index)}
                >
                  Skip
                </button>
              `
            : nothing}
        </div>

        ${step.hint && isActive
          ? html`
              <div class="hint">
                <span class="hint-label">Hint:</span> ${step.hint}
              </div>
            `
          : nothing}
      </div>
    `
  }

  private renderCompleteCard() {
    return html`
      <div class="step-card">
        <div class="complete">
          <div class="complete-icon">✓</div>
          <h2 class="complete-title">Tutorial Complete!</h2>
          <p class="complete-text">
            You've completed the ${this.state.tutorial.name} tutorial.
          </p>
          <button class="reset-button" @click=${this.handleReset}>
            Start Over
          </button>
        </div>
      </div>
    `
  }

  private renderSingleMode() {
    const { tutorial, currentStepIndex, isComplete } = this.state
    const currentStep = tutorial.steps[currentStepIndex]

    if (isComplete) {
      return html`
        <div class="container">
          <div class="complete">
            <div class="complete-icon">✓</div>
            <h2 class="complete-title">Tutorial Complete!</h2>
            <p class="complete-text">
              You've completed the ${tutorial.name} tutorial.
            </p>
            <button class="reset-button" @click=${this.handleReset}>
              Start Over
            </button>
          </div>
        </div>
      `
    }

    return html`
      <div class="container">
        <!-- Progress indicator -->
        <div class="progress">
          <div class="progress-text">
            Step ${currentStepIndex + 1} of ${tutorial.steps.length}
          </div>
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

          ${currentStep.command && !currentStep.requiresUserAction
            ? html`
                <div class="command-preview">
                  <code class="command-code">${currentStep.command}</code>
                </div>
              `
            : nothing}

          <div class="actions">
            ${!currentStep.requiresUserAction && currentStep.command
              ? html`
                  <button
                    class="show-me-button"
                    ?disabled=${this.isExecuting}
                    @click=${() => this.handleShowMe(currentStepIndex)}
                  >
                    ${this.isExecuting
                      ? currentStep.runningLabel || 'Running...'
                      : currentStep.showMeLabel || 'Show me'}
                  </button>
                `
              : nothing}
            ${currentStep.requiresUserAction
              ? html`
                  <div class="waiting-message">
                    Waiting for you to complete this step in the terminal...
                  </div>
                `
              : nothing}

            <button
              class="skip-button"
              ?disabled=${this.isExecuting}
              @click=${() => this.handleSkip(currentStepIndex)}
            >
              Skip
            </button>
          </div>

          ${currentStep.hint
            ? html`
                <div class="hint">
                  <span class="hint-label">Hint:</span> ${currentStep.hint}
                </div>
              `
            : nothing}
        </div>

        <!-- Step list -->
        <div class="step-list">
          ${tutorial.steps.map((step, index) =>
            this.renderStepIndicator(step, index, currentStepIndex)
          )}
        </div>
      </div>
    `
  }

  private renderStepIndicator(
    step: TutorialStep,
    index: number,
    currentIndex: number
  ) {
    const isComplete = index < currentIndex
    const isCurrent = index === currentIndex

    return html`
      <div
        class="step-indicator"
        style="opacity: ${isComplete || isCurrent ? 1 : 0.5}"
      >
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
