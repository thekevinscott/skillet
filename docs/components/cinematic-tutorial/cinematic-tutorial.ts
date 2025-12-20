import { LitElement, html, css } from 'lit'
import { property, state, query } from 'lit/decorators.js'
import { Terminal as XTerm } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import { WebContainer } from '@webcontainer/api'

export const TAG_NAME = 'skillet-cinematic-tutorial'

interface Scene {
  id: string
  title: string
  subtitle?: string
  content: string
  command?: string
  expectedOutput?: RegExp
  background?: string
  terminalHeight?: string
}

/**
 * Cinematic tutorial with full-screen scenes that transition
 * like a keynote presentation. Each scene has a terminal that
 * can demonstrate concepts.
 */
export class SkilletCinematicTutorial extends LitElement {
  static styles = css`
    :host {
      display: block;
    }

    .cinematic {
      position: fixed;
      inset: 0;
      background: #000;
      overflow: hidden;
      font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
    }

    /* Scene container */
    .scene {
      position: absolute;
      inset: 0;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 48px;
      opacity: 0;
      transform: translateY(40px);
      transition: all 0.6s cubic-bezier(0.16, 1, 0.3, 1);
      pointer-events: none;
    }

    .scene.active {
      opacity: 1;
      transform: translateY(0);
      pointer-events: all;
    }

    .scene.exiting {
      opacity: 0;
      transform: translateY(-40px);
    }

    /* Scene backgrounds */
    .scene.bg-gradient-blue {
      background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0f172a 100%);
    }

    .scene.bg-gradient-purple {
      background: linear-gradient(135deg, #1a1a2e 0%, #4a1942 50%, #1a1a2e 100%);
    }

    .scene.bg-gradient-green {
      background: linear-gradient(135deg, #0f1f1a 0%, #134e4a 50%, #0f1f1a 100%);
    }

    .scene.bg-dark {
      background: #0d1117;
    }

    /* Content */
    .scene-content {
      text-align: center;
      max-width: 800px;
      margin-bottom: 48px;
    }

    .scene-title {
      font-size: clamp(32px, 6vw, 72px);
      font-weight: 700;
      color: #fff;
      margin: 0 0 16px 0;
      line-height: 1.1;
      letter-spacing: -0.02em;
    }

    .scene-title .highlight {
      background: linear-gradient(135deg, #60a5fa, #a78bfa);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }

    .scene-subtitle {
      font-size: clamp(18px, 2.5vw, 24px);
      color: rgba(255, 255, 255, 0.7);
      margin: 0;
      line-height: 1.6;
    }

    /* Terminal in scene */
    .scene-terminal {
      width: 100%;
      max-width: 900px;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 25px 80px rgba(0, 0, 0, 0.5);
    }

    .terminal-chrome {
      background: #1e1e1e;
      padding: 12px 16px;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .terminal-dot {
      width: 12px;
      height: 12px;
      border-radius: 50%;
    }
    .terminal-dot.red { background: #ff5f56; }
    .terminal-dot.yellow { background: #ffbd2e; }
    .terminal-dot.green { background: #27c93f; }

    .terminal-container {
      background: #1e1e1e;
    }

    /* Navigation */
    .nav {
      position: fixed;
      bottom: 32px;
      left: 50%;
      transform: translateX(-50%);
      display: flex;
      align-items: center;
      gap: 24px;
      z-index: 100;
    }

    .nav-dots {
      display: flex;
      gap: 8px;
    }

    .nav-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.3);
      border: none;
      cursor: pointer;
      transition: all 0.3s ease;
    }

    .nav-dot:hover {
      background: rgba(255, 255, 255, 0.5);
    }

    .nav-dot.active {
      background: #fff;
      transform: scale(1.2);
    }

    .nav-btn {
      padding: 12px 24px;
      background: rgba(255, 255, 255, 0.1);
      border: 1px solid rgba(255, 255, 255, 0.2);
      color: #fff;
      border-radius: 8px;
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s ease;
      backdrop-filter: blur(8px);
    }

    .nav-btn:hover {
      background: rgba(255, 255, 255, 0.2);
    }

    .nav-btn.primary {
      background: #3b82f6;
      border-color: #3b82f6;
    }

    .nav-btn.primary:hover {
      background: #2563eb;
    }

    /* Action button in scene */
    .scene-action {
      margin-top: 24px;
    }

    .action-btn {
      padding: 16px 32px;
      background: linear-gradient(135deg, #3b82f6, #8b5cf6);
      border: none;
      color: #fff;
      border-radius: 12px;
      font-size: 18px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.3s ease;
      box-shadow: 0 8px 32px rgba(59, 130, 246, 0.3);
    }

    .action-btn:hover {
      transform: translateY(-2px);
      box-shadow: 0 12px 40px rgba(59, 130, 246, 0.4);
    }

    /* Keyboard hint */
    .keyboard-hint {
      position: fixed;
      bottom: 100px;
      left: 50%;
      transform: translateX(-50%);
      color: rgba(255, 255, 255, 0.4);
      font-size: 13px;
    }

    .keyboard-hint kbd {
      display: inline-block;
      padding: 4px 8px;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 4px;
      margin: 0 4px;
    }
  `

  @state() private currentScene = 0
  @state() private isTransitioning = false
  @state() private terminalReady = false

  @query('.terminal-container') private terminalContainer!: HTMLDivElement

  private xterm: XTerm | null = null
  private fitAddon: FitAddon | null = null
  private container: WebContainer | null = null
  private inputWriter: WritableStreamDefaultWriter | null = null

  private scenes: Scene[] = [
    {
      id: 'intro',
      title: 'Welcome to <span class="highlight">Skillet</span>',
      subtitle: 'Evaluation-driven Claude Code skill development',
      content: '',
      background: 'bg-gradient-blue',
    },
    {
      id: 'what-is',
      title: 'What is Skillet?',
      subtitle: 'A framework for teaching Claude Code new skills through iterative evaluation.',
      content: '',
      background: 'bg-gradient-purple',
    },
    {
      id: 'terminal-intro',
      title: 'Let\'s Try It',
      subtitle: 'This is your sandbox. Everything runs in your browser.',
      content: '',
      command: 'echo "Hello from Skillet!"',
      terminalHeight: '300px',
      background: 'bg-dark',
    },
    {
      id: 'explore',
      title: 'Explore Your Environment',
      subtitle: 'You have access to a full Node.js environment with npm.',
      content: '',
      command: 'ls -la && node --version',
      terminalHeight: '350px',
      background: 'bg-dark',
    },
    {
      id: 'create',
      title: 'Create Something',
      subtitle: 'Write code, run scripts, install packages.',
      content: '',
      command: 'echo \'console.log("Made with Skillet!")\' > app.js && node app.js',
      terminalHeight: '350px',
      background: 'bg-dark',
    },
    {
      id: 'next',
      title: 'Ready to Build?',
      subtitle: 'Get started with Skillet in your own project.',
      content: '',
      background: 'bg-gradient-green',
    },
  ]

  connectedCallback() {
    super.connectedCallback()
    window.addEventListener('keydown', this.handleKeydown)
  }

  disconnectedCallback() {
    super.disconnectedCallback()
    window.removeEventListener('keydown', this.handleKeydown)
    this.xterm?.dispose()
  }

  private handleKeydown = (e: KeyboardEvent) => {
    if (e.key === 'ArrowRight' || e.key === ' ') {
      this.nextScene()
    } else if (e.key === 'ArrowLeft') {
      this.prevScene()
    }
  }

  private async goToScene(index: number) {
    if (this.isTransitioning || index === this.currentScene) return
    if (index < 0 || index >= this.scenes.length) return

    this.isTransitioning = true

    // If going to a terminal scene and terminal not ready, boot it
    const targetScene = this.scenes[index]
    if (targetScene.command && !this.terminalReady) {
      await this.initTerminal()
    }

    this.currentScene = index

    setTimeout(() => {
      this.isTransitioning = false
    }, 600)
  }

  private nextScene() {
    this.goToScene(this.currentScene + 1)
  }

  private prevScene() {
    this.goToScene(this.currentScene - 1)
  }

  private async initTerminal() {
    await this.updateComplete

    if (!this.terminalContainer || this.xterm) return

    this.xterm = new XTerm({
      cursorBlink: true,
      fontSize: 15,
      fontFamily: '"JetBrains Mono", Menlo, Monaco, monospace',
      lineHeight: 1.4,
      theme: {
        background: '#1e1e1e',
        foreground: '#d4d4d4',
        cursor: '#fff',
      },
    })

    this.fitAddon = new FitAddon()
    this.xterm.loadAddon(this.fitAddon)
    this.xterm.open(this.terminalContainer)
    this.fitAddon.fit()

    this.xterm.writeln('\x1b[38;5;242m  Booting WebContainer...\x1b[0m')

    try {
      this.container = await WebContainer.boot()
      await this.container.mount({
        'hello.txt': { file: { contents: 'Hello, World!' } },
      })

      const shellProcess = await this.container.spawn('jsh', {
        terminal: { cols: this.xterm.cols, rows: this.xterm.rows },
      })

      shellProcess.output.pipeTo(
        new WritableStream({
          write: (data) => this.xterm?.write(data),
        })
      )

      this.inputWriter = shellProcess.input.getWriter()

      this.xterm.onData((data) => {
        this.inputWriter?.write(data)
      })

      new ResizeObserver(() => {
        this.fitAddon?.fit()
        shellProcess.resize({ cols: this.xterm!.cols, rows: this.xterm!.rows })
      }).observe(this.terminalContainer)

      this.terminalReady = true
      this.xterm.write('\r\x1b[K\x1b[38;5;40m  ✓ Ready\x1b[0m\n\n')
    } catch (err) {
      this.xterm.writeln(`\x1b[38;5;196m  Error: ${err}\x1b[0m`)
    }
  }

  private async runCommand(command: string) {
    if (!this.inputWriter) return

    for (const char of command) {
      await this.inputWriter.write(char)
      await new Promise((r) => setTimeout(r, 25))
    }
    await this.inputWriter.write('\n')
  }

  render() {
    return html`
      <div class="cinematic">
        ${this.scenes.map((scene, index) => html`
          <div
            class="scene ${scene.background || 'bg-dark'} ${index === this.currentScene ? 'active' : ''}"
          >
            <div class="scene-content">
              <h1 class="scene-title" .innerHTML=${scene.title}></h1>
              ${scene.subtitle ? html`<p class="scene-subtitle">${scene.subtitle}</p>` : ''}
            </div>

            ${scene.command ? html`
              <div class="scene-terminal" style="height: ${scene.terminalHeight || '300px'}">
                <div class="terminal-chrome">
                  <span class="terminal-dot red"></span>
                  <span class="terminal-dot yellow"></span>
                  <span class="terminal-dot green"></span>
                </div>
                <div class="terminal-container" style="height: calc(${scene.terminalHeight || '300px'} - 40px)"></div>
              </div>
              <div class="scene-action">
                <button
                  class="action-btn"
                  @click=${() => this.runCommand(scene.command!)}
                  ?disabled=${!this.terminalReady}
                >
                  ${this.terminalReady ? `Run: ${scene.command}` : 'Loading...'}
                </button>
              </div>
            ` : ''}

            ${scene.id === 'intro' ? html`
              <div class="scene-action">
                <button class="action-btn" @click=${() => this.nextScene()}>
                  Get Started →
                </button>
              </div>
            ` : ''}

            ${scene.id === 'next' ? html`
              <div class="scene-action">
                <button class="action-btn" @click=${() => window.location.href = '/getting-started'}>
                  Read the Docs →
                </button>
              </div>
            ` : ''}
          </div>
        `)}

        <nav class="nav">
          <button class="nav-btn" @click=${this.prevScene} ?disabled=${this.currentScene === 0}>
            ← Back
          </button>
          <div class="nav-dots">
            ${this.scenes.map((_, i) => html`
              <button
                class="nav-dot ${i === this.currentScene ? 'active' : ''}"
                @click=${() => this.goToScene(i)}
              ></button>
            `)}
          </div>
          <button
            class="nav-btn primary"
            @click=${this.nextScene}
            ?disabled=${this.currentScene === this.scenes.length - 1}
          >
            Next →
          </button>
        </nav>

        <div class="keyboard-hint">
          <kbd>←</kbd> <kbd>→</kbd> or <kbd>Space</kbd> to navigate
        </div>
      </div>
    `
  }
}
