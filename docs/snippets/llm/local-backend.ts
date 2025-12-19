/**
 * Local LLM (WebLLM) backend implementation.
 */

import type { LLMBackend, LLMBackendStatus, Message, StreamEvent } from './backend';
import { LocalLLMClient, AVAILABLE_MODELS, type ModelId } from '../webllm';

export { AVAILABLE_MODELS, type ModelId };

export class LocalLLMBackend implements LLMBackend {
  readonly id = 'local';
  readonly name = 'Local LLM';
  readonly description = 'Browser-based inference (no API key)';

  private client: LocalLLMClient | null = null;
  private selectedModel: ModelId = 'Phi-3.5-mini-instruct-q4f16_1-MLC';
  private status: LLMBackendStatus = { state: 'ready' };
  private statusListeners: Set<(status: LLMBackendStatus) => void> = new Set();
  private webGPUSupported: boolean | null = null;

  async isAvailable(): Promise<boolean> {
    if (this.webGPUSupported !== null) {
      return this.webGPUSupported;
    }

    this.webGPUSupported = await LocalLLMClient.isSupported();

    if (!this.webGPUSupported) {
      this.updateStatus({
        state: 'unavailable',
        message: 'WebGPU not supported in this browser',
      });
    }

    return this.webGPUSupported;
  }

  getStatus(): LLMBackendStatus {
    return this.status;
  }

  /**
   * Get the currently selected model.
   */
  getSelectedModel(): ModelId {
    return this.selectedModel;
  }

  /**
   * Set the model to use.
   */
  setModel(modelId: ModelId): void {
    this.selectedModel = modelId;
    // Reset client if model changed
    if (this.client) {
      this.client = null;
      this.updateStatus({ state: 'ready' });
    }
  }

  async initialize(): Promise<void> {
    if (!(await this.isAvailable())) {
      throw new Error('WebGPU not supported');
    }

    this.updateStatus({
      state: 'initializing',
      message: 'Loading model...',
      progress: 0,
    });

    try {
      this.client = new LocalLLMClient(this.selectedModel, {
        onProgress: (progress) => {
          this.updateStatus({
            state: 'initializing',
            message: progress.text,
            progress: progress.progress,
          });
        },
      });

      await this.client.initialize();
      this.updateStatus({ state: 'active' });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load model';
      this.updateStatus({ state: 'error', message });
      throw err;
    }
  }

  async *stream(
    messages: Message[],
    options?: { system?: string }
  ): AsyncGenerator<StreamEvent> {
    if (!this.client) {
      yield { type: 'error', error: 'Model not loaded' };
      return;
    }

    for await (const event of this.client.stream(messages, options)) {
      yield event;
    }
  }

  /**
   * Reset the chat context.
   */
  async reset(): Promise<void> {
    if (this.client) {
      await this.client.reset();
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

export default LocalLLMBackend;
