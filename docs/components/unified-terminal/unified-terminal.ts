import { LitElement, html, unsafeCSS } from 'lit'
import { property, state, query } from 'lit/decorators.js'
import '../terminal/index.js'
import '../api-key-input/index.js'
import type { SkilletTerminal } from '../terminal/terminal.js'
import { BackendRegistry, type LLMBackendStatus, type Message } from '../../services/llm/backend.js'
import { ClaudeBackend } from '../../services/llm/claude-backend.js'
import { LocalLLMBackend, AVAILABLE_MODELS, type ModelId } from '../../services/llm/local-backend.js'
import styles from './unified-terminal.css?raw'

export const TAG_NAME = 'skillet-unified-terminal'

type BackendId = 'claude' | 'local'

/**
 * Unified terminal with multiple LLM backend support.
 * Allows switching between Claude API and local WebLLM.
 */
export class SkilletUnifiedTerminal extends LitElement {
  static styles = unsafeCSS(styles)

  @property({ type: String }) height = '400px'
  @property({ type: String }) systemPrompt = 'You are a helpful assistant.'
  @property({ type: String }) defaultBackend: BackendId = 'claude'

  @state() private activeBackend: BackendId = 'claude'
  @state() private backendStatuses: Map<string, LLMBackendStatus> = new Map()
  @state() private selectedModel: ModelId = 'Phi-3.5-mini-instruct-q4f16_1-MLC'
  @state() private isWebGPUSupported = true
  @state() private isStreaming = false

  @query('skillet-terminal') private terminal!: SkilletTerminal

  private registry = new BackendRegistry()
  private claudeBackend = new ClaudeBackend()
  private localBackend = new LocalLLMBackend()
  private unsubscribe?: () => void

  async connectedCallback() {
    super.connectedCallback()

    // Register backends
    this.registry.register(this.claudeBackend)
    this.registry.register(this.localBackend)

    // Check WebGPU support
    this.isWebGPUSupported = await this.localBackend.isAvailable()

    // Initialize statuses
    this.backendStatuses.set('claude', this.claudeBackend.getStatus())
    this.backendStatuses.set('local', this.localBackend.getStatus())

    // Subscribe to status changes
    this.unsubscribe = this.registry.onStatusChange((id, status) => {
      this.backendStatuses = new Map(this.backendStatuses).set(id, status)
    })

    // Set default backend
    this.activeBackend = this.defaultBackend
  }

  disconnectedCallback() {
    super.disconnectedCallback()
    this.unsubscribe?.()
  }

  private handleBackendSwitch(id: BackendId) {
    if (id === 'local' && !this.isWebGPUSupported) return
    this.activeBackend = id
    this.registry.clearConversation()
  }

  private handleModelChange(e: Event) {
    const select = e.target as HTMLSelectElement
    this.selectedModel = select.value as ModelId
    this.localBackend.setModel(this.selectedModel)
  }

  private async handleLoadModel() {
    try {
      await this.localBackend.initialize()
    } catch {
      // Error handled via status
    }
  }

  private handleKeySaved(e: CustomEvent) {
    this.claudeBackend.setApiKey(e.detail.key)
    this.backendStatuses = new Map(this.backendStatuses).set('claude', this.claudeBackend.getStatus())
  }

  private handleKeyCleared() {
    this.claudeBackend.setApiKey(null)
    this.backendStatuses = new Map(this.backendStatuses).set('claude', this.claudeBackend.getStatus())
  }

  private async handleUserInput(command: string, writeOutput: (text: string) => void): Promise<boolean> {
    // Special commands
    if (command.trim() === '/clear') {
      this.registry.clearConversation()
      if (this.activeBackend === 'local') {
        await this.localBackend.reset()
      }
      writeOutput('\r\n[Conversation cleared]\r\n')
      return true
    }

    if (command.trim() === '/help') {
      writeOutput('\r\nCommands:\r\n')
      writeOutput('  /clear - Clear conversation history\r\n')
      writeOutput('  /help  - Show this help\r\n')
      writeOutput(`\r\nCurrent backend: ${this.activeBackend}\r\n`)
      return true
    }

    // Get active backend
    const backend = this.activeBackend === 'claude' ? this.claudeBackend : this.localBackend
    const status = backend.getStatus()

    // Check if ready
    if (status.state !== 'active') {
      if (this.activeBackend === 'claude') {
        writeOutput('\r\n[Please enter your API key first]\r\n')
      } else {
        writeOutput('\r\n[Please load a model first]\r\n')
      }
      return true
    }

    // Add message and stream
    this.registry.addMessage({ role: 'user', content: command })
    this.isStreaming = true
    writeOutput('\r\n')

    try {
      let response = ''
      for await (const event of backend.stream(this.registry.getConversation(), { system: this.systemPrompt })) {
        if (event.type === 'text' && event.text) {
          response += event.text
          const text = event.text.replace(/\n/g, '\r\n')
          writeOutput(text)
        } else if (event.type === 'error') {
          writeOutput(`\r\n[Error: ${event.error}]\r\n`)
        }
      }
      this.registry.addMessage({ role: 'assistant', content: response })
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

  private getStatusDotClass(status: LLMBackendStatus): string {
    switch (status.state) {
      case 'active': return 'active'
      case 'initializing': return 'initializing'
      case 'ready': return 'ready'
      case 'error': return 'error'
      default: return 'unavailable'
    }
  }

  private getStatusText(backend: BackendId): string {
    const status = this.backendStatuses.get(backend)
    if (!status) return 'Unknown'

    if (backend === 'claude') {
      return this.claudeBackend.hasApiKey() ? 'Connected' : 'No API key'
    }

    switch (status.state) {
      case 'active': return 'Model loaded'
      case 'initializing': return status.message || 'Loading...'
      case 'ready': return 'Ready'
      case 'error': return 'Error'
      default: return 'Unavailable'
    }
  }

  render() {
    const claudeStatus = this.backendStatuses.get('claude') || { state: 'ready' }
    const localStatus = this.backendStatuses.get('local') || { state: 'ready' }

    return html`
      <div class="container">
        <div class="header">
          <span class="title">LLM Terminal</span>

          <div class="backend-tabs">
            <button
              class="backend-tab ${this.activeBackend === 'claude' ? 'active' : ''}"
              @click=${() => this.handleBackendSwitch('claude')}
            >Claude API</button>
            <button
              class="backend-tab ${this.activeBackend === 'local' ? 'active' : ''}"
              ?disabled=${!this.isWebGPUSupported}
              @click=${() => this.handleBackendSwitch('local')}
            >Local LLM</button>
          </div>
        </div>

        ${this.activeBackend === 'claude' ? html`
          <!-- Claude Configuration -->
          ${!this.claudeBackend.hasApiKey() ? html`
            <skillet-api-key-input
              @key-saved=${this.handleKeySaved}
              @key-cleared=${this.handleKeyCleared}
            ></skillet-api-key-input>
          ` : html`
            <div class="status-row" style="padding: 0 4px;">
              <div class="status-dot active"></div>
              <span class="status-text">Claude API connected</span>
            </div>
          `}
        ` : html`
          <!-- Local LLM Configuration -->
          ${!this.isWebGPUSupported ? html`
            <div class="error-box">
              WebGPU is not supported in your browser. Please use Chrome, Edge, or Firefox with WebGPU enabled.
            </div>
          ` : localStatus.state === 'active' ? html`
            <div class="status-row" style="padding: 0 4px;">
              <div class="status-dot active"></div>
              <span class="status-text">Model loaded</span>
            </div>
          ` : html`
            <div class="config-section">
              <div class="config-row">
                <span class="config-label">Model</span>
                <select
                  class="model-select"
                  .value=${this.selectedModel}
                  @change=${this.handleModelChange}
                  ?disabled=${localStatus.state === 'initializing'}
                >
                  ${AVAILABLE_MODELS.map(model => html`
                    <option value=${model.id}>${model.name} (${model.size})</option>
                  `)}
                </select>
                <button
                  class="action-button"
                  @click=${this.handleLoadModel}
                  ?disabled=${localStatus.state === 'initializing'}
                >
                  ${localStatus.state === 'initializing' ? 'Loading...' : 'Load'}
                </button>
              </div>

              ${localStatus.state === 'initializing' && localStatus.progress !== undefined ? html`
                <div class="progress-bar">
                  <div class="progress-fill" style="width: ${localStatus.progress * 100}%"></div>
                </div>
                <div class="progress-text">${localStatus.message}</div>
              ` : ''}

              <div class="warning" style="margin-top: 12px">
                First load downloads the model (~1-2GB). Runs entirely in your browser.
              </div>
            </div>
          `}
        `}

        <div class="prompt-hint">
          Type a message and press Enter. Use /help for commands.
        </div>

        <skillet-terminal
          height=${this.height}
        ></skillet-terminal>
      </div>
    `
  }
}
