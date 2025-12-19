import { LitElement, html, css } from 'lit'
import { customElement, state } from 'lit/decorators.js'

const API_KEY_STORAGE_KEY = 'anthropic_api_key'

/**
 * API key input component with localStorage persistence.
 * Allows users to enter and save their Anthropic API key.
 */
@customElement('skillet-api-key-input')
export class SkilletApiKeyInput extends LitElement {
  static styles = css`
    :host {
      display: block;
    }

    .container {
      padding: 16px;
      background: #fafafa;
      border-radius: 8px;
      border: 1px solid #e5e7eb;
    }

    .label {
      display: block;
      font-size: 14px;
      font-weight: 500;
      color: #374151;
      margin-bottom: 8px;
    }

    .input-row {
      display: flex;
      gap: 8px;
    }

    .input {
      flex: 1;
      padding: 10px 12px;
      border: 1px solid #d1d5db;
      border-radius: 6px;
      font-size: 14px;
      font-family: Menlo, Monaco, 'Courier New', monospace;
    }

    .input:focus {
      outline: none;
      border-color: #8B7355;
      box-shadow: 0 0 0 2px rgba(139, 115, 85, 0.2);
    }

    .input.has-key {
      background: #f0fdf4;
      border-color: #86efac;
    }

    .save-button {
      padding: 10px 16px;
      background: #8B7355;
      color: white;
      border: none;
      border-radius: 6px;
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
    }

    .save-button:hover {
      background: #7a6349;
    }

    .save-button:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .clear-button {
      padding: 10px 16px;
      background: transparent;
      color: #6b7280;
      border: 1px solid #d1d5db;
      border-radius: 6px;
      font-size: 14px;
      cursor: pointer;
    }

    .clear-button:hover {
      background: #f3f4f6;
    }

    .status {
      margin-top: 8px;
      font-size: 12px;
      color: #6b7280;
    }

    .status.saved {
      color: #059669;
    }

    .help-text {
      margin-top: 8px;
      font-size: 12px;
      color: #6b7280;
    }

    .help-text a {
      color: #8B7355;
    }
  `

  @state() private apiKey = ''
  @state() private hasStoredKey = false
  @state() private showStatus = false

  connectedCallback() {
    super.connectedCallback()
    this.loadStoredKey()
  }

  private loadStoredKey() {
    if (typeof window !== 'undefined') {
      const storedKey = localStorage.getItem(API_KEY_STORAGE_KEY)
      if (storedKey) {
        this.apiKey = storedKey
        this.hasStoredKey = true
      }
    }
  }

  private handleInput(e: Event) {
    const input = e.target as HTMLInputElement
    this.apiKey = input.value
    this.showStatus = false
  }

  private handleSave() {
    if (!this.apiKey.trim()) return

    if (typeof window !== 'undefined') {
      localStorage.setItem(API_KEY_STORAGE_KEY, this.apiKey.trim())
      this.hasStoredKey = true
      this.showStatus = true

      this.dispatchEvent(new CustomEvent('key-saved', {
        detail: { key: this.apiKey.trim() },
        bubbles: true,
        composed: true
      }))

      // Hide status after delay
      setTimeout(() => {
        this.showStatus = false
      }, 3000)
    }
  }

  private handleClear() {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(API_KEY_STORAGE_KEY)
      this.apiKey = ''
      this.hasStoredKey = false
      this.showStatus = false

      this.dispatchEvent(new CustomEvent('key-cleared', {
        bubbles: true,
        composed: true
      }))
    }
  }

  private handleKeyDown(e: KeyboardEvent) {
    if (e.key === 'Enter') {
      this.handleSave()
    }
  }

  // Public API
  getApiKey(): string | null {
    return this.hasStoredKey ? this.apiKey : null
  }

  hasKey(): boolean {
    return this.hasStoredKey
  }

  render() {
    return html`
      <div class="container">
        <label class="label">Anthropic API Key</label>
        <div class="input-row">
          <input
            type="password"
            class="input ${this.hasStoredKey ? 'has-key' : ''}"
            placeholder="sk-ant-..."
            .value=${this.apiKey}
            @input=${this.handleInput}
            @keydown=${this.handleKeyDown}
          />
          ${this.hasStoredKey ? html`
            <button class="clear-button" @click=${this.handleClear}>Clear</button>
          ` : html`
            <button
              class="save-button"
              ?disabled=${!this.apiKey.trim()}
              @click=${this.handleSave}
            >Save</button>
          `}
        </div>
        ${this.showStatus ? html`
          <div class="status saved">API key saved to browser storage</div>
        ` : ''}
        <div class="help-text">
          Get your API key from the
          <a href="https://console.anthropic.com/settings/keys" target="_blank" rel="noopener">
            Anthropic Console
          </a>.
          Keys are stored locally in your browser.
        </div>
      </div>
    `
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'skillet-api-key-input': SkilletApiKeyInput
  }
}
