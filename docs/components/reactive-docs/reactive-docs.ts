import { LitElement, html, unsafeCSS } from 'lit'
import { property, state, query } from 'lit/decorators.js'
import type { Tutorial, TutorialState, TutorialAction } from '../../services/tutorial-types.js'
import { tutorialReducer, createInitialState } from '../../services/tutorial-types.js'
import '../terminal/index.js'
import '../docs-panel/index.js'
import type { SkilletTerminal } from '../terminal/terminal.js'
import styles from './reactive-docs.css?raw'

export const TAG_NAME = 'skillet-reactive-docs'

/**
 * Reactive documentation layout with split-pane view.
 * Docs panel on the left, terminal on the right.
 */
export class SkilletReactiveDocs extends LitElement {
  static styles = unsafeCSS(styles)

  @property({ type: String }) height = '600px'

  @state() private tutorialState: TutorialState
  @state() private isTerminalReady = false

  @query('skillet-terminal') private terminal!: SkilletTerminal

  private outputBuffer = ''
  private advanceTimeout: ReturnType<typeof setTimeout> | null = null

  // Default tutorial for demo
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

  private dispatch(action: TutorialAction) {
    this.tutorialState = tutorialReducer(this.tutorialState, action)
  }

  private handleTerminalReady() {
    this.isTerminalReady = true
  }

  private handleTerminalOutput(data: string) {
    this.outputBuffer += data
    this.dispatch({ type: 'OUTPUT', data })

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
        }, 1000)
      }
    }
  }

  private async handleShowMe() {
    const currentStep = this.tutorialState.tutorial.steps[this.tutorialState.currentStepIndex]
    if (!currentStep?.command || !this.terminal?.isReady()) return

    this.dispatch({ type: 'EXECUTE_START' })
    this.outputBuffer = ''

    try {
      await this.terminal.executeCommand(currentStep.command)

      // If no watch pattern, advance after a delay
      if (!currentStep.watchPattern && !currentStep.validate) {
        setTimeout(() => {
          this.dispatch({ type: 'ADVANCE' })
        }, 1500)
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Command failed'
      this.dispatch({ type: 'ERROR', message })
    }
  }

  private handleSkip() {
    this.dispatch({ type: 'SKIP' })
    this.outputBuffer = ''
  }

  private handleReset() {
    this.dispatch({ type: 'RESET' })
    this.outputBuffer = ''
  }

  disconnectedCallback() {
    super.disconnectedCallback()
    if (this.advanceTimeout) {
      clearTimeout(this.advanceTimeout)
    }
  }

  render() {
    return html`
      <div class="container" style="height: ${this.height}">
        <div class="docs-pane">
          <skillet-docs-panel
            .state=${this.tutorialState}
            .isExecuting=${this.tutorialState.isExecuting}
            @show-me=${this.handleShowMe}
            @skip=${this.handleSkip}
            @reset=${this.handleReset}
          ></skillet-docs-panel>
        </div>

        <div class="terminal-pane">
          ${!this.isTerminalReady ? html`
            <div class="terminal-loading">
              <div class="spinner"></div>
              <span>Initializing terminal...</span>
            </div>
          ` : ''}

          <skillet-terminal
            height="100%"
            .files=${this.tutorialState.tutorial.files || {}}
            @terminal-ready=${this.handleTerminalReady}
            .onOutput=${(data: string) => this.handleTerminalOutput(data)}
          ></skillet-terminal>
        </div>
      </div>
    `
  }
}
