/**
 * WebLLM client for browser-based local LLM inference.
 * Provides the same interface as claude.ts for consistency.
 */

import type { MLCEngine } from '@mlc-ai/web-llm';

export interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface StreamEvent {
  type: 'text' | 'done' | 'error' | 'progress';
  text?: string;
  error?: string;
  progress?: {
    text: string;
    progress: number;
  };
}

export type ModelId =
  | 'Phi-3.5-mini-instruct-q4f16_1-MLC'
  | 'Qwen2.5-1.5B-Instruct-q4f16_1-MLC'
  | 'Llama-3.2-1B-Instruct-q4f16_1-MLC'
  | 'SmolLM2-1.7B-Instruct-q4f16_1-MLC';

// Small models suitable for browser use
export const AVAILABLE_MODELS: { id: ModelId; name: string; size: string }[] = [
  { id: 'Phi-3.5-mini-instruct-q4f16_1-MLC', name: 'Phi-3.5 Mini', size: '~2GB' },
  { id: 'Qwen2.5-1.5B-Instruct-q4f16_1-MLC', name: 'Qwen 2.5 1.5B', size: '~1GB' },
  { id: 'SmolLM2-1.7B-Instruct-q4f16_1-MLC', name: 'SmolLM2 1.7B', size: '~1GB' },
];

export class LocalLLMClient {
  private engine: MLCEngine | null = null;
  private modelId: ModelId;
  private onProgress?: (progress: { text: string; progress: number }) => void;

  constructor(
    modelId: ModelId = 'Phi-3.5-mini-instruct-q4f16_1-MLC',
    options?: { onProgress?: (progress: { text: string; progress: number }) => void }
  ) {
    this.modelId = modelId;
    this.onProgress = options?.onProgress;
  }

  /**
   * Check if WebGPU is supported in this browser.
   */
  static async isSupported(): Promise<boolean> {
    if (typeof navigator === 'undefined') return false;
    if (!('gpu' in navigator)) return false;
    try {
      const adapter = await navigator.gpu.requestAdapter();
      return adapter !== null;
    } catch {
      return false;
    }
  }

  /**
   * Initialize the engine and load the model.
   * This can take a while on first load (model download).
   */
  async initialize(): Promise<void> {
    const { CreateMLCEngine } = await import('@mlc-ai/web-llm');

    this.engine = await CreateMLCEngine(this.modelId, {
      initProgressCallback: (progress) => {
        if (this.onProgress) {
          this.onProgress({
            text: progress.text,
            progress: progress.progress,
          });
        }
      },
    });
  }

  /**
   * Check if the engine is ready.
   */
  isReady(): boolean {
    return this.engine !== null;
  }

  /**
   * Send a message and stream the response.
   * Matches the interface of ClaudeClient.stream()
   */
  async *stream(
    messages: Message[],
    options?: { system?: string }
  ): AsyncGenerator<StreamEvent> {
    if (!this.engine) {
      yield { type: 'error', error: 'Engine not initialized. Call initialize() first.' };
      return;
    }

    try {
      const allMessages: Message[] = [];

      if (options?.system) {
        allMessages.push({ role: 'system', content: options.system });
      }
      allMessages.push(...messages);

      const chunks = await this.engine.chat.completions.create({
        messages: allMessages,
        stream: true,
      });

      for await (const chunk of chunks) {
        const content = chunk.choices[0]?.delta?.content;
        if (content) {
          yield { type: 'text', text: content };
        }
      }

      yield { type: 'done' };
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      yield { type: 'error', error: message };
    }
  }

  /**
   * Send a message and get a complete response.
   * Matches the interface of ClaudeClient.complete()
   */
  async complete(
    messages: Message[],
    options?: { system?: string }
  ): Promise<{ content: string }> {
    if (!this.engine) {
      throw new Error('Engine not initialized. Call initialize() first.');
    }

    const allMessages: Message[] = [];

    if (options?.system) {
      allMessages.push({ role: 'system', content: options.system });
    }
    allMessages.push(...messages);

    const response = await this.engine.chat.completions.create({
      messages: allMessages,
    });

    return {
      content: response.choices[0]?.message?.content || '',
    };
  }

  /**
   * Reset the chat context.
   */
  async reset(): Promise<void> {
    if (this.engine) {
      await this.engine.resetChat();
    }
  }
}

export default LocalLLMClient;
