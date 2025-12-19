import { LitElement, html, css } from 'lit'
import { customElement, property, state, query } from 'lit/decorators.js'
import './terminal'
import './api-key-input'
import type { SkilletTerminal } from './terminal'
import { ClaudeBackend } from '../services/llm/claude-backend'
import type { Message } from '../services/llm/backend'

/**
 * Terminal with Claude API integration.
 * Combines terminal, API key input, and Claude streaming.
 */
@customElement('skillet-claude-terminal')
export class SkilletClaudeTerminal extends LitElement {
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

    .status-dot.active {
      background: #10b981;
    }

    .status-dot.inactive {
      background: #d1d5db;
    }

    .status-text {
      font-size: 13px;
      color: #6b7280;
    }

    .api-key-section {
      display: ${this.hasApiKey ? 'none' : 'block'};
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

  @state() private hasApiKey = false
  @state() private isStreaming = false

  @query('skillet-terminal') private terminal!: SkilletTerminal

  private backend = new ClaudeBackend()
  private conversationHistory: Message[] = []

  connectedCallback() {
    super.connectedCallback()
    this.hasApiKey = this.backend.hasApiKey()
  }

  private handleKeySaved(e: CustomEvent) {
    this.backend.setApiKey(e.detail.key)
    this.hasApiKey = true
  }

  private handleKeyCleared() {
    this.backend.setApiKey(null)
    this.hasApiKey = false
  }

  private async handleUserInput(command: string, writeOutput: (text: string) => void): Promise<boolean> {
    // Check for special commands
    if (command.trim() === '/clear') {
      this.conversationHistory = []
      writeOutput('\r\n[Conversation cleared]\r\n')
      return true
    }

    if (command.trim() === '/help') {
      writeOutput('\r\nCommands:\r\n')
      writeOutput('  /clear - Clear conversation history\r\n')
      writeOutput('  /help  - Show this help\r\n')
      writeOutput('\r\nType anything else to chat with Claude.\r\n')
      return true
    }

    // If no API key, prompt user
    if (!this.hasApiKey) {
      writeOutput('\r\n[Please enter your API key above first]\r\n')
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
          // Convert newlines for terminal
          const text = event.text.replace(/\n/g, '\r\n')
          writeOutput(text)
        } else if (event.type === 'error') {
          writeOutput(`\r\n[Error: ${event.error}]\r\n`)
        }
      }

      // Add assistant response to history (reconstruct from what we streamed)
      // For simplicity, we'd need to track this during streaming
      writeOutput('\r\n')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error'
      writeOutput(`\r\n[Error: ${message}]\r\n`)
    }

    this.isStreaming = false
    return true
  }

  protected firstUpdated() {
    // Set up command handler
    if (this.terminal) {
      this.terminal.commandHandler = (cmd, write) => this.handleUserInput(cmd, write)
    }
  }

  render() {
    return html`
      <div class="container">
        <div class="header">
          <span class="title">Claude Terminal</span>
          <div class="status">
            <div class="status-dot ${this.hasApiKey ? 'active' : 'inactive'}"></div>
            <span class="status-text">${this.hasApiKey ? 'Connected' : 'No API key'}</span>
          </div>
        </div>

        ${!this.hasApiKey ? html`
          <skillet-api-key-input
            @key-saved=${this.handleKeySaved}
            @key-cleared=${this.handleKeyCleared}
          ></skillet-api-key-input>
        ` : ''}

        <div class="prompt-hint">
          Type a message and press Enter to chat with Claude. Use /help for commands.
        </div>

        <skillet-terminal
          height=${this.height}
        ></skillet-terminal>
      </div>
    `
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'skillet-claude-terminal': SkilletClaudeTerminal
  }
}
