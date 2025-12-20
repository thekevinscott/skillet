import { LitElement, html, css } from 'lit'
import { property, state, query } from 'lit/decorators.js'
import { Terminal as XTerm } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import { WebContainer } from '@webcontainer/api'

export const TAG_NAME = 'skillet-immersive-terminal'

interface TutorialHint {
  text: string
  command?: string
  delay?: number
}

/**
 * Immersive terminal where docs ARE the terminal.
 * Instructions appear as styled output within the terminal itself.
 */
export class SkilletImmersiveTerminal extends LitElement {
  static styles = css`
    :host {
      display: block;
      height: 100%;
      min-height: 500px;
    }

    .immersive-container {
      height: 100%;
      display: flex;
      flex-direction: column;
      background: #0d1117;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
    }

    .terminal-header {
      display: flex;
      align-items: center;
      padding: 12px 16px;
      background: #161b22;
      border-bottom: 1px solid #30363d;
    }

    .traffic-lights {
      display: flex;
      gap: 8px;
    }

    .dot {
      width: 12px;
      height: 12px;
      border-radius: 50%;
    }
    .dot.red { background: #ff5f56; }
    .dot.yellow { background: #ffbd2e; }
    .dot.green { background: #27c93f; }

    .header-title {
      flex: 1;
      text-align: center;
      font-size: 13px;
      color: #8b949e;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }

    .progress-bar {
      display: flex;
      gap: 4px;
      padding: 0 16px;
    }

    .progress-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #30363d;
      transition: all 0.3s ease;
    }

    .progress-dot.active {
      background: #58a6ff;
      box-shadow: 0 0 8px #58a6ff;
    }

    .progress-dot.complete {
      background: #3fb950;
    }

    .terminal-body {
      flex: 1;
      min-height: 0;
      position: relative;
    }

    .terminal-container {
      height: 100%;
    }

    /* Floating hint card */
    .hint-card {
      position: absolute;
      bottom: 80px;
      left: 50%;
      transform: translateX(-50%);
      background: linear-gradient(135deg, #1f6feb 0%, #388bfd 100%);
      color: white;
      padding: 16px 24px;
      border-radius: 12px;
      max-width: 400px;
      box-shadow: 0 8px 32px rgba(31, 111, 235, 0.3);
      animation: float-in 0.4s ease-out;
      z-index: 10;
    }

    .hint-card.success {
      background: linear-gradient(135deg, #238636 0%, #2ea043 100%);
      box-shadow: 0 8px 32px rgba(46, 160, 67, 0.3);
    }

    .hint-card h3 {
      margin: 0 0 8px 0;
      font-size: 14px;
      font-weight: 600;
      opacity: 0.9;
    }

    .hint-card p {
      margin: 0;
      font-size: 15px;
      line-height: 1.5;
    }

    .hint-card code {
      background: rgba(255, 255, 255, 0.2);
      padding: 2px 8px;
      border-radius: 4px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 13px;
    }

    .hint-card .try-btn {
      margin-top: 12px;
      padding: 8px 16px;
      background: rgba(255, 255, 255, 0.2);
      border: 1px solid rgba(255, 255, 255, 0.3);
      color: white;
      border-radius: 6px;
      font-size: 13px;
      cursor: pointer;
      transition: background 0.2s;
    }

    .hint-card .try-btn:hover {
      background: rgba(255, 255, 255, 0.3);
    }

    .hint-card .dismiss {
      position: absolute;
      top: 8px;
      right: 12px;
      background: none;
      border: none;
      color: rgba(255, 255, 255, 0.6);
      cursor: pointer;
      font-size: 18px;
    }

    @keyframes float-in {
      from {
        opacity: 0;
        transform: translateX(-50%) translateY(20px);
      }
      to {
        opacity: 1;
        transform: translateX(-50%) translateY(0);
      }
    }

    /* Welcome overlay */
    .welcome-overlay {
      position: absolute;
      inset: 0;
      background: rgba(13, 17, 23, 0.95);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      z-index: 20;
      animation: fade-in 0.5s ease-out;
    }

    .welcome-overlay h1 {
      font-size: 48px;
      font-weight: 700;
      color: #f0f6fc;
      margin: 0 0 16px 0;
      font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
    }

    .welcome-overlay p {
      font-size: 18px;
      color: #8b949e;
      margin: 0 0 32px 0;
    }

    .start-btn {
      padding: 16px 48px;
      font-size: 18px;
      font-weight: 600;
      background: linear-gradient(135deg, #238636 0%, #2ea043 100%);
      color: white;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      transition: transform 0.2s, box-shadow 0.2s;
    }

    .start-btn:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(46, 160, 67, 0.4);
    }

    @keyframes fade-in {
      from { opacity: 0; }
      to { opacity: 1; }
    }
  `

  @property({ type: String }) height = '600px'

  @state() private status: 'welcome' | 'booting' | 'ready' | 'complete' = 'welcome'
  @state() private currentStep = 0
  @state() private showHint = false
  @state() private hintContent: TutorialHint | null = null

  @query('.terminal-container') private terminalContainer!: HTMLDivElement

  private xterm: XTerm | null = null
  private fitAddon: FitAddon | null = null
  private container: WebContainer | null = null
  private inputWriter: WritableStreamDefaultWriter | null = null
  private currentLine = ''
  private outputBuffer = ''

  private steps: TutorialHint[] = [
    {
      text: "Welcome! Let's start with a classic. Type the command below or click 'Try it'",
      command: 'echo "Hello, World!"',
    },
    {
      text: "Nice! Now let's see what files are in your workspace.",
      command: 'ls -la',
    },
    {
      text: "There's a file called greeting.js. Let's see what's inside.",
      command: 'cat greeting.js',
    },
    {
      text: 'Now run it with Node.js!',
      command: 'node greeting.js',
    },
    {
      text: "Let's create something new. Make your own file:",
      command: 'echo "I made this!" > myfile.txt && cat myfile.txt',
    },
  ]

  private async startTutorial() {
    this.status = 'booting'
    await this.initTerminal()
  }

  private async initTerminal() {
    this.xterm = new XTerm({
      cursorBlink: true,
      fontSize: 15,
      fontFamily: '"JetBrains Mono", "Fira Code", Menlo, Monaco, monospace',
      lineHeight: 1.4,
      theme: {
        background: '#0d1117',
        foreground: '#c9d1d9',
        cursor: '#58a6ff',
        cursorAccent: '#0d1117',
        selectionBackground: '#388bfd44',
        black: '#484f58',
        red: '#ff7b72',
        green: '#3fb950',
        yellow: '#d29922',
        blue: '#58a6ff',
        magenta: '#bc8cff',
        cyan: '#39c5cf',
        white: '#b1bac4',
      },
    })

    this.fitAddon = new FitAddon()
    this.xterm.loadAddon(this.fitAddon)
    this.xterm.open(this.terminalContainer)
    this.fitAddon.fit()

    // Styled welcome message
    this.writeStyled('\n  ╭─────────────────────────────────────╮\n', 'blue')
    this.writeStyled('  │  ', 'blue')
    this.writeStyled('🚀 Skillet Interactive Tutorial', 'white')
    this.writeStyled('    │\n', 'blue')
    this.writeStyled('  ╰─────────────────────────────────────╯\n\n', 'blue')
    this.writeStyled('  Booting WebContainer...', 'dim')

    try {
      this.container = await WebContainer.boot()

      await this.container.mount({
        'greeting.js': { file: { contents: 'console.log("🎉 Welcome to Skillet!");' } },
        'hello.txt': { file: { contents: 'Hello from the filesystem!' } },
      })

      const shellProcess = await this.container.spawn('jsh', {
        terminal: { cols: this.xterm.cols, rows: this.xterm.rows },
      })

      shellProcess.output.pipeTo(
        new WritableStream({
          write: (data) => {
            this.xterm?.write(data)
            this.outputBuffer += data
            this.checkStepCompletion()
          },
        })
      )

      this.inputWriter = shellProcess.input.getWriter()

      this.xterm.onData((data) => {
        if (data === '\r') {
          this.currentLine = ''
          this.outputBuffer = ''
        } else if (data === '\x7f') {
          this.currentLine = this.currentLine.slice(0, -1)
        } else {
          this.currentLine += data
        }
        this.inputWriter?.write(data)
      })

      // Handle resize
      new ResizeObserver(() => {
        this.fitAddon?.fit()
        shellProcess.resize({ cols: this.xterm!.cols, rows: this.xterm!.rows })
      }).observe(this.terminalContainer)

      this.xterm.write('\r\x1b[K') // Clear the booting message
      this.writeStyled('\n  ✓ Ready!\n\n', 'green')

      this.status = 'ready'

      // Show first hint after a moment
      setTimeout(() => {
        this.showStepHint(0)
      }, 800)

    } catch (err) {
      this.writeStyled(`\n  ✗ Error: ${err}\n`, 'red')
    }
  }

  private writeStyled(text: string, color: string) {
    const colors: Record<string, string> = {
      blue: '\x1b[38;5;39m',
      green: '\x1b[38;5;40m',
      red: '\x1b[38;5;196m',
      yellow: '\x1b[38;5;220m',
      white: '\x1b[38;5;255m',
      dim: '\x1b[38;5;242m',
      reset: '\x1b[0m',
    }
    this.xterm?.write(`${colors[color] || ''}${text}${colors.reset}`)
  }

  private showStepHint(stepIndex: number) {
    if (stepIndex >= this.steps.length) {
      this.status = 'complete'
      this.hintContent = {
        text: "🎉 You've completed the tutorial! You now know the basics of working in a terminal.",
      }
      this.showHint = true
      return
    }

    this.currentStep = stepIndex
    this.hintContent = this.steps[stepIndex]
    this.showHint = true
  }

  private checkStepCompletion() {
    const step = this.steps[this.currentStep]
    if (!step?.command) return

    // Simple check: if the expected command output appears
    const triggers: Record<number, RegExp> = {
      0: /Hello, World!/,
      1: /greeting\.js/,
      2: /Welcome to Skillet/,
      3: /🎉/,
      4: /I made this!/,
    }

    if (triggers[this.currentStep]?.test(this.outputBuffer)) {
      this.showHint = false
      setTimeout(() => {
        this.showStepHint(this.currentStep + 1)
      }, 1000)
    }
  }

  private async runSuggestedCommand() {
    if (!this.hintContent?.command || !this.inputWriter) return

    // Type out the command
    for (const char of this.hintContent.command) {
      await this.inputWriter.write(char)
      await new Promise((r) => setTimeout(r, 30))
    }
    await this.inputWriter.write('\n')
  }

  private dismissHint() {
    this.showHint = false
  }

  render() {
    return html`
      <div class="immersive-container" style="height: ${this.height}">
        <div class="terminal-header">
          <div class="traffic-lights">
            <span class="dot red"></span>
            <span class="dot yellow"></span>
            <span class="dot green"></span>
          </div>
          <span class="header-title">Skillet — Interactive Terminal</span>
          <div class="progress-bar">
            ${this.steps.map(
              (_, i) => html`
                <span
                  class="progress-dot ${i < this.currentStep ? 'complete' : ''} ${i === this.currentStep ? 'active' : ''}"
                ></span>
              `
            )}
          </div>
        </div>

        <div class="terminal-body">
          <div class="terminal-container"></div>

          ${this.status === 'welcome'
            ? html`
                <div class="welcome-overlay">
                  <h1>Learn by Doing</h1>
                  <p>An interactive terminal tutorial — no docs, just code.</p>
                  <button class="start-btn" @click=${this.startTutorial}>
                    Start Tutorial →
                  </button>
                </div>
              `
            : ''}

          ${this.showHint && this.hintContent
            ? html`
                <div class="hint-card ${this.status === 'complete' ? 'success' : ''}">
                  <button class="dismiss" @click=${this.dismissHint}>×</button>
                  <h3>Step ${this.currentStep + 1} of ${this.steps.length}</h3>
                  <p>${this.hintContent.text}</p>
                  ${this.hintContent.command
                    ? html`
                        <p><code>${this.hintContent.command}</code></p>
                        <button class="try-btn" @click=${this.runSuggestedCommand}>
                          Try it →
                        </button>
                      `
                    : ''}
                </div>
              `
            : ''}
        </div>
      </div>
    `
  }
}
