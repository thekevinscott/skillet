import { LitElement, html, unsafeCSS } from 'lit'
import { state } from 'lit/decorators.js'
import styles from './api-key-input.css?raw'

export const TAG_NAME = 'skillet-api-key-input'

const API_KEY_STORAGE_KEY = 'anthropic_api_key'

/**
 * API key input component with localStorage persistence.
 * Allows users to enter and save their Anthropic API key.
 */
export class SkilletApiKeyInput extends LitElement {
  static styles = unsafeCSS(styles)

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
