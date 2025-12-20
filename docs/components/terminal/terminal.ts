import { LitElement, html, unsafeCSS } from 'lit'
import { property, state, query } from 'lit/decorators.js'
import { Terminal as XTerm } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import { WebContainer } from '@webcontainer/api'
import styles from './terminal.css?raw'

export const TAG_NAME = 'skillet-terminal'

type TerminalStatus = 'booting' | 'ready' | 'error'

/**
 * Interactive terminal component with WebContainer sandboxed execution.
 *
 * Usage:
 * ```html
 * <skillet-terminal height="400px"></skillet-terminal>
 * ```
 */
export class SkilletTerminal extends LitElement {
  static styles = unsafeCSS(styles)

  @property({ type: String }) height = '400px'
  @property({ type: Object }) files: Record<string, string> = {}
  @property({ type: Array }) initialCommands: string[] = []

  @state() private status: TerminalStatus = 'booting'
  @state() private error: string | null = null

  @query('.terminal-container') private terminalContainer!: HTMLDivElement

  private xterm: XTerm | null = null
  private fitAddon: FitAddon | null = null
  private container: WebContainer | null = null
  private inputWriter: WritableStreamDefaultWriter | null = null
  private currentLine = ''
  private mounted = true

  // Custom command handler (set by parent components)
  public commandHandler?: (command: string, writeOutput: (text: string) => void) => boolean

  // Callback for terminal output
  public onOutput?: (data: string) => void

  async connectedCallback() {
    super.connectedCallback()
    this.mounted = true
  }

  disconnectedCallback() {
    super.disconnectedCallback()
    this.mounted = false
    this.xterm?.dispose()
  }

  protected async firstUpdated() {
    await this.initTerminal()
  }

  private async initTerminal() {
    try {
      // Initialize xterm.js
      this.xterm = new XTerm({
        cursorBlink: true,
        fontSize: 14,
        fontFamily: 'Menlo, Monaco, "Courier New", monospace',
        theme: {
          background: '#1a1a1a',
          foreground: '#d4d4d4',
          cursor: '#d4d4d4',
          cursorAccent: '#1a1a1a',
          selectionBackground: '#264f78',
        },
      })

      this.fitAddon = new FitAddon()
      this.xterm.loadAddon(this.fitAddon)

      this.xterm.open(this.terminalContainer)
      this.fitAddon.fit()

      this.xterm.writeln('Booting WebContainer...\r\n')

      // Boot WebContainer
      this.container = await WebContainer.boot()
      if (!this.mounted) return

      // Mount files
      if (Object.keys(this.files).length > 0) {
        const fileTree: Record<string, { file: { contents: string } }> = {}
        for (const [path, contents] of Object.entries(this.files)) {
          fileTree[path] = { file: { contents } }
        }
        await this.container.mount(fileTree)
      }

      // Start shell
      const shellProcess = await this.container.spawn('jsh', {
        terminal: { cols: this.xterm.cols, rows: this.xterm.rows },
      })

      // Connect shell output to terminal
      shellProcess.output.pipeTo(
        new WritableStream({
          write: (data) => {
            this.xterm?.write(data)
            this.onOutput?.(data)
          },
        })
      )

      // Connect terminal input to shell
      this.inputWriter = shellProcess.input.getWriter()

      // Handle input with optional command interception
      this.xterm.onData((data) => {
        // Handle Enter key
        if (data === '\r') {
          const command = this.currentLine
          this.currentLine = ''

          // Check if custom handler wants this command
          if (this.commandHandler && command.trim()) {
            const writeOutput = (text: string) => this.xterm?.write(text)
            const handled = this.commandHandler(command, writeOutput)
            if (handled) {
              this.xterm?.write('\r\n')
              return
            }
          }

          // Pass to shell
          this.inputWriter?.write(data)
        }
        // Handle backspace
        else if (data === '\x7f') {
          if (this.currentLine.length > 0) {
            this.currentLine = this.currentLine.slice(0, -1)
            this.inputWriter?.write(data)
          }
        }
        // Regular character
        else {
          this.currentLine += data
          this.inputWriter?.write(data)
        }
      })

      // Handle resize
      const resizeObserver = new ResizeObserver(() => {
        this.fitAddon?.fit()
        shellProcess.resize({ cols: this.xterm!.cols, rows: this.xterm!.rows })
      })
      resizeObserver.observe(this.terminalContainer)

      this.status = 'ready'

      // Run initial commands
      for (const cmd of this.initialCommands) {
        await this.sleep(500)
        await this.executeCommand(cmd)
      }

      // Dispatch ready event
      this.dispatchEvent(new CustomEvent('terminal-ready'))

    } catch (err) {
      if (!this.mounted) return
      const message = err instanceof Error ? err.message : 'Unknown error'
      this.error = message
      this.status = 'error'
      this.xterm?.writeln(`\r\nError: ${message}`)
    }
  }

  // Public methods for programmatic control

  /**
   * Type text character by character with animation
   * Note: We only write to inputWriter, not xterm directly,
   * because the shell echoes input back to the terminal.
   */
  async typeText(text: string, delay = 50): Promise<void> {
    if (!this.inputWriter) return

    for (const char of text) {
      await this.inputWriter.write(char)
      await this.sleep(delay)
    }
  }

  /**
   * Execute a command with typing animation
   */
  async executeCommand(command: string, delay = 50): Promise<void> {
    await this.typeText(command, delay)
    await this.typeText('\n', 0)
  }

  /**
   * Write text directly to terminal (no animation)
   */
  write(text: string): void {
    this.xterm?.write(text)
  }

  /**
   * Check if terminal is ready
   */
  isReady(): boolean {
    return this.status === 'ready'
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  render() {
    return html`
      <div class="terminal-wrapper">
        ${this.status === 'booting' ? html`
          <div class="terminal-status">Booting...</div>
        ` : ''}

        ${this.status === 'error' && this.error ? html`
          <div class="terminal-error">${this.error}</div>
        ` : ''}

        <div
          class="terminal-container"
          style="height: ${this.height}"
        ></div>
      </div>
    `
  }
}
