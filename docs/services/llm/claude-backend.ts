/**
 * Claude API backend implementation.
 */

import type { LLMBackend, LLMBackendStatus, Message, StreamEvent } from './backend';
import { ClaudeClient } from '../claude';

const API_KEY_STORAGE_KEY = 'anthropic_api_key';

export class ClaudeBackend implements LLMBackend {
  readonly id = 'claude';
  readonly name = 'Claude';
  readonly description = 'Anthropic Claude API (requires API key)';

  private client: ClaudeClient | null = null;
  private status: LLMBackendStatus = { state: 'ready' };
  private statusListeners: Set<(status: LLMBackendStatus) => void> = new Set();

  constructor() {
    // Check if API key exists in localStorage
    if (typeof window !== 'undefined') {
      const savedKey = localStorage.getItem(API_KEY_STORAGE_KEY);
      if (savedKey) {
        this.client = new ClaudeClient(savedKey);
        this.status = { state: 'active' };
      }
    }
  }

  async isAvailable(): Promise<boolean> {
    // Claude API is always potentially available (just needs API key)
    return true;
  }

  getStatus(): LLMBackendStatus {
    return this.status;
  }

  /**
   * Set the API key.
   */
  setApiKey(key: string | null): void {
    if (key) {
      this.client = new ClaudeClient(key);
      if (typeof window !== 'undefined') {
        localStorage.setItem(API_KEY_STORAGE_KEY, key);
      }
      this.updateStatus({ state: 'active' });
    } else {
      this.client = null;
      if (typeof window !== 'undefined') {
        localStorage.removeItem(API_KEY_STORAGE_KEY);
      }
      this.updateStatus({ state: 'ready' });
    }
  }

  /**
   * Check if API key is configured.
   */
  hasApiKey(): boolean {
    return this.client !== null;
  }

  async initialize(): Promise<void> {
    // No-op for Claude - just needs API key
    if (this.client) {
      this.updateStatus({ state: 'active' });
    }
  }

  async *stream(
    messages: Message[],
    options?: { system?: string }
  ): AsyncGenerator<StreamEvent> {
    if (!this.client) {
      yield { type: 'error', error: 'API key not configured' };
      return;
    }

    // Filter out system messages (handled via options)
    const chatMessages = messages
      .filter((m) => m.role !== 'system')
      .map((m) => ({ role: m.role as 'user' | 'assistant', content: m.content }));

    for await (const event of this.client.stream(chatMessages, options)) {
      // Map Claude events to our unified format
      if (event.type === 'text') {
        yield { type: 'text', text: event.text };
      } else if (event.type === 'done') {
        yield { type: 'done' };
      } else if (event.type === 'error') {
        yield { type: 'error', error: event.error };
      }
    }
  }

  onStatusChange(callback: (status: LLMBackendStatus) => void): () => void {
    this.statusListeners.add(callback);
    return () => this.statusListeners.delete(callback);
  }

  private updateStatus(status: LLMBackendStatus): void {
    this.status = status;
    for (const listener of this.statusListeners) {
      listener(status);
    }
  }
}

export default ClaudeBackend;
