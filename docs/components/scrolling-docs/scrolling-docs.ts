import { LitElement, html, unsafeCSS, css, nothing } from 'lit'
import { property, state } from 'lit/decorators.js'
import type { Tutorial, TutorialStep, TutorialState, TutorialAction } from '../../services/tutorial-types.js'
import { tutorialReducer, createInitialState } from '../../services/tutorial-types.js'
import { docsEventBus } from '../../services/event-bus.js'
import { PatternMatcher } from '../../services/reactivity/pattern-matcher.js'
import { StepObserver } from '../../services/reactivity/step-observer.js'
import styles from './scrolling-docs.css?raw'

export const TAG_NAME = 'skillet-scrolling-docs'

/**
 * Scrollable documentation component for Layout A (viewport-fixed terminal).
 *
 * This component renders tutorial steps as a scrollable list in the main
 * content area while communicating with a viewport-fixed terminal via events.
 */
export class SkilletScrollingDocs extends LitElement {
  static styles = unsafeCSS(styles)

  @state() private tutorialState: TutorialState
  @state() private visibleStepIndex = 0
  @state() private isTerminalReady = false

  private outputBuffer = ''
  private advanceTimeout: ReturnType<typeof setTimeout> | null = null
  private patternMatcher = new PatternMatcher()
  private stepObserver: StepObserver | null = null
  private unsubscribers: Array<() => void> = []

  // Default tutorial
  private defaultTutorial: Tutorial = {
    id: 'hello-world',
    name: 'Hello World',
    description: 'A simple introduction to the reactive docs system.',
    files: {
      'hello.txt': 'Hello, World!',
      'greeting.js': 'console.log("Welcome to Skillet!");',
    },
    steps: [
      {
        id: 'intro',
        title: 'Welcome to Skillet',
        description: "Let's explore the reactive docs system. We'll run some simple commands to see how it works.",
        command: 'echo "Hello from the terminal!"',
        showMeLabel: 'Show me',
        runningLabel: 'Running...',
      },
      {
        id: 'list-files',
        title: 'See your files',
        description: "We've pre-loaded some files in the terminal. Let's see what's here.",
        command: 'ls -la',
        showMeLabel: 'List files',
        runningLabel: 'Listing...',
      },
      {
        id: 'read-file',
        title: 'Read a file',
        description: "Now let's read the contents of hello.txt.",
        command: 'cat hello.txt',
        showMeLabel: 'Read file',
        runningLabel: 'Reading...',
        watchPattern: /Hello, World!/,
      },
      {
        id: 'run-script',
        title: 'Run a script',
        description: "Let's run the greeting.js script to see JavaScript in action.",
        command: 'node greeting.js',
        showMeLabel: 'Run script',
        runningLabel: 'Running...',
        watchPattern: /Welcome to Skillet!/,
      },
      {
        id: 'complete',
        title: 'Great job!',
        description: "You've completed the Hello World tutorial! You now know how the reactive docs system works.",
        command: 'echo "Tutorial complete!"',
        showMeLabel: 'Finish',
      },
    ],
  }

  constructor() {
    super()
    this.tutorialState = createInitialState(this.defaultTutorial)
  }

  connectedCallback() {
    super.connectedCallback()
    this.setupEventListeners()
    this.setupStepObserver()
  }

  disconnectedCallback() {
    super.disconnectedCallback()
    this.unsubscribers.forEach((unsub) => unsub())
    this.unsubscribers = []
    this.stepObserver?.destroy()
    this.stepObserver = null
    if (this.advanceTimeout) {
      clearTimeout(this.advanceTimeout)
    }
  }

  private setupEventListeners() {
    // Listen for terminal events
    this.unsubscribers.push(
      docsEventBus.on('terminal:ready', () => {
        this.isTerminalReady = true
      })
    )

    this.unsubscribers.push(
      docsEventBus.on('terminal:output', (data) => {
        this.handleTerminalOutput(data)
      })
    )
  }

  private setupStepObserver() {
    this.stepObserver = new StepObserver({
      root: null, // viewport
      rootMargin: '-20% 0px -60% 0px',
      threshold: [0, 0.25, 0.5, 0.75, 1],
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

    const steps = this.shadowRoot?.querySelectorAll('.step-section')
    steps?.forEach((step, index) => {
      const tutorial = this.tutorialState.tutorial.steps[index]
      if (tutorial) {
        this.stepObserver!.observe(step, index, tutorial.id)
      }
    })
  }

  firstUpdated() {
    // Observe step elements after first render
    this.observeStepElements()
  }

  updated(changedProps: Map<string, unknown>) {
    if (changedProps.has('tutorialState')) {
      // Re-observe if tutorial changes
      this.observeStepElements()
    }
  }

  private dispatch(action: TutorialAction) {
    this.tutorialState = tutorialReducer(this.tutorialState, action)
  }

  private handleTerminalOutput(data: string) {
    this.outputBuffer += data
    this.dispatch({ type: 'OUTPUT', data })

    // Check pattern matcher for errors
    const matches = this.patternMatcher.processOutput(data)
    for (const match of matches) {
      if (match.type === 'error') {
        docsEventBus.emit('error:detected', {
          message: match.message || 'Unknown error',
          suggestion: match.suggestion,
        })
      }
    }

    // Check if we should auto-advance
    const currentStep = this.tutorialState.tutorial.steps[this.tutorialState.currentStepIndex]
    if (currentStep && this.tutorialState.isExecuting) {
      const shouldAdvance =
        (currentStep.watchPattern && currentStep.watchPattern.test(this.outputBuffer)) ||
        (currentStep.validate && currentStep.validate(this.outputBuffer))

      if (shouldAdvance) {
        if (this.advanceTimeout) {
          clearTimeout(this.advanceTimeout)
        }
        this.advanceTimeout = setTimeout(() => {
          this.dispatch({ type: 'ADVANCE' })
          this.outputBuffer = ''
          this.patternMatcher.clearBuffer()

          docsEventBus.emit('step:complete', {
            index: this.tutorialState.currentStepIndex - 1,
            stepId: currentStep.id,
          })

          // Scroll to next step
          this.scrollToStep(this.tutorialState.currentStepIndex)
        }, 1000)
      }
    }
  }

  private scrollToStep(index: number) {
    const steps = this.shadowRoot?.querySelectorAll('.step-section')
    if (steps && steps[index]) {
      steps[index].scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  private async handleShowMe(stepIndex: number) {
    const step = this.tutorialState.tutorial.steps[stepIndex]
    if (!step?.command || !this.isTerminalReady) return

    // Only allow executing current step
    if (stepIndex !== this.tutorialState.currentStepIndex) {
      return
    }

    this.dispatch({ type: 'EXECUTE_START' })
    this.outputBuffer = ''
    this.patternMatcher.clearBuffer()

    // Send command to terminal via event bus
    docsEventBus.emit('docs:execute', step.command)

    // Note: Terminal will emit output events that we listen for
    // If no watch pattern, advance after delay
    if (!step.watchPattern && !step.validate) {
      setTimeout(() => {
        this.dispatch({ type: 'ADVANCE' })
        docsEventBus.emit('step:complete', {
          index: this.tutorialState.currentStepIndex - 1,
          stepId: step.id,
        })
        this.scrollToStep(this.tutorialState.currentStepIndex)
      }, 2000)
    }
  }

  private handleSkip(stepIndex: number) {
    if (stepIndex !== this.tutorialState.currentStepIndex) return

    this.dispatch({ type: 'SKIP' })
    this.outputBuffer = ''
    this.patternMatcher.clearBuffer()
    this.scrollToStep(this.tutorialState.currentStepIndex)
  }

  private handleReset() {
    this.dispatch({ type: 'RESET' })
    this.outputBuffer = ''
    this.patternMatcher.clearBuffer()
    this.scrollToStep(0)
  }

  render() {
    const { tutorial, currentStepIndex, isComplete } = this.tutorialState

    return html`
      <div class="scrolling-docs">
        <!-- Progress header -->
        <div class="progress-header">
          <div class="progress-info">
            <span class="tutorial-name">${tutorial.name}</span>
            <span class="step-counter">
              ${isComplete
                ? 'Complete!'
                : `Step ${currentStepIndex + 1} of ${tutorial.steps.length}`}
            </span>
          </div>
          <div class="progress-dots">
            ${tutorial.steps.map((_, index) => {
              const isCompleted = index < currentStepIndex || isComplete
              const isActive = index === this.visibleStepIndex
              return html`
                <button
                  class="progress-dot ${isCompleted ? 'completed' : ''} ${isActive ? 'active' : ''}"
                  @click=${() => this.scrollToStep(index)}
                  title="Step ${index + 1}"
                ></button>
              `
            })}
          </div>
        </div>

        <!-- Scrollable steps -->
        <div class="steps-container">
          ${tutorial.steps.map((step, index) =>
            this.renderStep(step, index, currentStepIndex, isComplete)
          )}

          ${isComplete ? this.renderComplete() : nothing}
        </div>
      </div>
    `
  }

  private renderStep(
    step: TutorialStep,
    index: number,
    currentStepIndex: number,
    isComplete: boolean
  ) {
    const isCompleted = index < currentStepIndex || isComplete
    const isActive = index === currentStepIndex && !isComplete
    const isPending = index > currentStepIndex && !isComplete

    const getStatus = () => {
      if (isCompleted) return 'completed'
      if (isActive) return 'active'
      return 'pending'
    }

    return html`
      <section
        class="step-section ${getStatus()}"
        data-step-id=${step.id}
        data-step-index=${index}
      >
        <div class="step-marker">
          <div class="step-number ${getStatus()}">
            ${isCompleted ? html`<span class="checkmark">✓</span>` : index + 1}
          </div>
          <div class="step-line"></div>
        </div>

        <div class="step-content">
          <h3 class="step-title">${step.title}</h3>
          <p class="step-description">${step.description}</p>

          ${step.command && !step.requiresUserAction
            ? html`
                <div class="command-block">
                  <code>${step.command}</code>
                </div>
              `
            : nothing}

          <div class="step-actions">
            ${!step.requiresUserAction && step.command && !isCompleted
              ? html`
                  <button
                    class="btn-primary"
                    ?disabled=${this.tutorialState.isExecuting || isPending || !this.isTerminalReady}
                    @click=${() => this.handleShowMe(index)}
                  >
                    ${this.tutorialState.isExecuting && isActive
                      ? step.runningLabel || 'Running...'
                      : step.showMeLabel || 'Show me'}
                  </button>
                `
              : nothing}

            ${step.requiresUserAction && isActive
              ? html`
                  <div class="waiting-badge">
                    Waiting for you to complete this step in the terminal...
                  </div>
                `
              : nothing}

            ${isActive && !isCompleted
              ? html`
                  <button
                    class="btn-secondary"
                    ?disabled=${this.tutorialState.isExecuting}
                    @click=${() => this.handleSkip(index)}
                  >
                    Skip
                  </button>
                `
              : nothing}
          </div>

          ${step.hint && isActive
            ? html`
                <div class="hint-box">
                  <strong>Hint:</strong> ${step.hint}
                </div>
              `
            : nothing}
        </div>
      </section>
    `
  }

  private renderComplete() {
    return html`
      <section class="complete-section">
        <div class="complete-content">
          <div class="complete-icon">🎉</div>
          <h3 class="complete-title">Tutorial Complete!</h3>
          <p class="complete-text">
            You've successfully completed the ${this.tutorialState.tutorial.name} tutorial.
          </p>
          <button class="btn-primary" @click=${this.handleReset}>
            Start Over
          </button>
        </div>
      </section>
    `
  }
}
