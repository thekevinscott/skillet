import { LitElement, html, css } from 'lit'
import { customElement, property, state, query } from 'lit/decorators.js'
import './terminal'
import type { SkilletTerminal } from './terminal'
import { LocalLLMBackend, AVAILABLE_MODELS, type ModelId } from '../services/llm/local-backend'
import type { Message, LLMBackendStatus } from '../services/llm/backend'

/**
 * Terminal with local WebLLM inference.
 * Runs models entirely in the browser using WebGPU.
 */
@customElement('skillet-local-llm-terminal')
export class SkilletLocalLLMTerminal extends LitElement {
  static styles = css`
    :host {
      display: block;
    }

    .container {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 16px;
      background: #fafafa;
      border: 1px solid #e5e7eb;
      border-radius: 8px;
    }

    .title {
      font-size: 16px;
      font-weight: 600;
      color: #111827;
    }

    .status {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
    }

    .status-dot.active { background: #10b981; }
    .status-dot.initializing { background: #f59e0b; }
    .status-dot.ready { background: #3b82f6; }
    .status-dot.error { background: #ef4444; }
    .status-dot.unavailable { background: #d1d5db; }

    .status-text {
      font-size: 13px;
      color: #6b7280;
    }

    .model-section {
      padding: 16px;
      background: #fafafa;
      border: 1px solid #e5e7eb;
      border-radius: 8px;
    }

    .model-label {
      font-size: 14px;
      font-weight: 500;
      color: #374151;
      margin-bottom: 8px;
    }

    .model-select {
      width: 100%;
      padding: 10px 12px;
      border: 1px solid #d1d5db;
      border-radius: 6px;
      font-size: 14px;
      margin-bottom: 12px;
    }

    .model-select:focus {
      outline: none;
      border-color: #8B7355;
    }

    .load-button {
      width: 100%;
      padding: 12px 24px;
      background: #8B7355;
      color: white;
      border: none;
      border-radius: 8px;
      font-size: 16px;
      font-weight: 500;
      cursor: pointer;
    }

    .load-button:hover {
      background: #7a6349;
    }

    .load-button:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .progress-bar {
      height: 8px;
      background: #e5e7eb;
      border-radius: 4px;
      overflow: hidden;
      margin-top: 12px;
    }

    .progress-fill {
      height: 100%;
      background: #8B7355;
      transition: width 0.3s ease;
    }

    .progress-text {
      font-size: 12px;
      color: #6b7280;
      margin-top: 8px;
    }

    .warning {
      padding: 12px 16px;
      background: #fef3c7;
      color: #92400e;
      border-radius: 8px;
      font-size: 14px;
    }

    .error-box {
      padding: 12px 16px;
      background: #fee2e2;
      color: #dc2626;
      border-radius: 8px;
      font-size: 14px;
    }

    .prompt-hint {
      padding: 12px 16px;
      background: #eff6ff;
      border-radius: 8px;
      font-size: 14px;
      color: #1e40af;
      margin-bottom: 8px;
    }
  `

  @property({ type: String }) height = '400px'
  @property({ type: String }) systemPrompt = 'You are a helpful assistant.'

  @state() private status: LLMBackendStatus = { state: 'ready' }
  @state() private selectedModel: ModelId = 'Phi-3.5-mini-instruct-q4f16_1-MLC'
  @state() private isWebGPUSupported = true
  @state() private isStreaming = false

  @query('skillet-terminal') private terminal!: SkilletTerminal

  private backend = new LocalLLMBackend()
  private conversationHistory: Message[] = []
  private unsubscribe?: () => void

  async connectedCallback() {
    super.connectedCallback()

    // Check WebGPU support
    this.isWebGPUSupported = await this.backend.isAvailable()
    this.status = this.backend.getStatus()

    // Subscribe to status changes
    this.unsubscribe = this.backend.onStatusChange((status) => {
      this.status = status
    })
  }

  disconnectedCallback() {
    super.disconnectedCallback()
    this.unsubscribe?.()
  }

  private handleModelChange(e: Event) {
    const select = e.target as HTMLSelectElement
    this.selectedModel = select.value as ModelId
    this.backend.setModel(this.selectedModel)
  }

  private async handleLoadModel() {
    try {
      await this.backend.initialize()
    } catch (err) {
      // Error is handled via status callback
    }
  }

  private async handleUserInput(command: string, writeOutput: (text: string) => void): Promise<boolean> {
    // Check for special commands
    if (command.trim() === '/clear') {
      this.conversationHistory = []
      await this.backend.reset()
      writeOutput('\r\n[Conversation cleared]\r\n')
      return true
    }

    if (command.trim() === '/help') {
      writeOutput('\r\nCommands:\r\n')
      writeOutput('  /clear - Clear conversation history\r\n')
      writeOutput('  /help  - Show this help\r\n')
      writeOutput('\r\nType anything else to chat with the local model.\r\n')
      return true
    }

    // If model not loaded, prompt user
    if (this.status.state !== 'active') {
      writeOutput('\r\n[Please load a model first]\r\n')
      return true
    }

    // Add user message to history
    this.conversationHistory.push({ role: 'user', content: command })

    // Stream response
    this.isStreaming = true
    writeOutput('\r\n')

    try {
      for await (const event of this.backend.stream(this.conversationHistory, { system: this.systemPrompt })) {
        if (event.type === 'text' && event.text) {
          const text = event.text.replace(/\n/g, '\r\n')
          writeOutput(text)
        } else if (event.type === 'error') {
          writeOutput(`\r\n[Error: ${event.error}]\r\n`)
        }
      }
      writeOutput('\r\n')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error'
      writeOutput(`\r\n[Error: ${message}]\r\n`)
    }

    this.isStreaming = false
    return true
  }

  protected firstUpdated() {
    if (this.terminal) {
      this.terminal.commandHandler = (cmd, write) => this.handleUserInput(cmd, write)
    }
  }

  private getStatusDotClass(): string {
    switch (this.status.state) {
      case 'active': return 'active'
      case 'initializing': return 'initializing'
      case 'ready': return 'ready'
      case 'error': return 'error'
      default: return 'unavailable'
    }
  }

  private getStatusText(): string {
    switch (this.status.state) {
      case 'active': return 'Model loaded'
      case 'initializing': return this.status.message || 'Loading...'
      case 'ready': return 'Ready to load'
      case 'error': return 'Error'
      default: return 'Unavailable'
    }
  }

  render() {
    if (!this.isWebGPUSupported) {
      return html`
        <div class="container">
          <div class="error-box">
            WebGPU is not supported in your browser. Local LLM inference requires WebGPU.
            Please use Chrome, Edge, or Firefox with WebGPU enabled.
          </div>
        </div>
      `
    }

    return html`
      <div class="container">
        <div class="header">
          <span class="title">Local LLM Terminal</span>
          <div class="status">
            <div class="status-dot ${this.getStatusDotClass()}"></div>
            <span class="status-text">${this.getStatusText()}</span>
          </div>
        </div>

        ${this.status.state === 'ready' || this.status.state === 'initializing' ? html`
          <div class="model-section">
            <div class="model-label">Select Model</div>
            <select
              class="model-select"
              .value=${this.selectedModel}
              @change=${this.handleModelChange}
              ?disabled=${this.status.state === 'initializing'}
            >
              ${AVAILABLE_MODELS.map(model => html`
                <option value=${model.id}>${model.name} (${model.size})</option>
              `)}
            </select>

            <button
              class="load-button"
              @click=${this.handleLoadModel}
              ?disabled=${this.status.state === 'initializing'}
            >
              ${this.status.state === 'initializing' ? 'Loading...' : 'Load Model'}
            </button>

            ${this.status.state === 'initializing' && this.status.progress !== undefined ? html`
              <div class="progress-bar">
                <div class="progress-fill" style="width: ${this.status.progress * 100}%"></div>
              </div>
              <div class="progress-text">${this.status.message}</div>
            ` : ''}

            <div class="warning" style="margin-top: 12px">
              Note: First load downloads the model (~1-2GB). This runs entirely in your browser.
            </div>
          </div>
        ` : ''}

        ${this.status.state === 'error' ? html`
          <div class="error-box">${this.status.message}</div>
        ` : ''}

        ${this.status.state === 'active' ? html`
          <div class="prompt-hint">
            Type a message and press Enter to chat. Use /help for commands.
          </div>
        ` : ''}

        <skillet-terminal
          height=${this.height}
        ></skillet-terminal>
      </div>
    `
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'skillet-local-llm-terminal': SkilletLocalLLMTerminal
  }
}
