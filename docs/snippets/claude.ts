/**
 * Lightweight Claude client for browser environments.
 *
 * Note: The Anthropic API doesn't support browser CORS by default.
 * This client can work with:
 * 1. A CORS proxy (set CORS_PROXY_URL)
 * 2. Your own backend proxy
 * 3. Direct calls if you've configured CORS headers
 */

export interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export interface ClaudeResponse {
  content: string;
  stopReason: 'end_turn' | 'tool_use' | 'max_tokens';
  toolUse?: {
    name: string;
    input: Record<string, unknown>;
  };
}

export interface StreamEvent {
  type: 'text' | 'tool_use' | 'done' | 'error';
  text?: string;
  toolName?: string;
  toolInput?: Record<string, unknown>;
  error?: string;
}

const ANTHROPIC_API_URL = 'https://api.anthropic.com/v1/messages';

export class ClaudeClient {
  private apiKey: string;
  private corsProxy?: string;

  constructor(apiKey: string, options?: { corsProxy?: string }) {
    this.apiKey = apiKey;
    this.corsProxy = options?.corsProxy;
  }

  private getUrl(): string {
    if (this.corsProxy) {
      return `${this.corsProxy}${ANTHROPIC_API_URL}`;
    }
    return ANTHROPIC_API_URL;
  }

  /**
   * Send a message to Claude and stream the response.
   */
  async *stream(
    messages: Message[],
    options?: {
      model?: string;
      maxTokens?: number;
      system?: string;
    }
  ): AsyncGenerator<StreamEvent> {
    const model = options?.model ?? 'claude-sonnet-4-20250514';
    const maxTokens = options?.maxTokens ?? 4096;

    try {
      const response = await fetch(this.getUrl(), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': this.apiKey,
          'anthropic-version': '2023-06-01',
          'anthropic-dangerous-direct-browser-access': 'true',
        },
        body: JSON.stringify({
          model,
          max_tokens: maxTokens,
          system: options?.system,
          messages,
          stream: true,
        }),
      });

      if (!response.ok) {
        const error = await response.text();
        yield { type: 'error', error: `API error: ${response.status} - ${error}` };
        return;
      }

      const reader = response.body?.getReader();
      if (!reader) {
        yield { type: 'error', error: 'No response body' };
        return;
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') {
              yield { type: 'done' };
              return;
            }

            try {
              const event = JSON.parse(data);

              if (event.type === 'content_block_delta') {
                if (event.delta?.type === 'text_delta') {
                  yield { type: 'text', text: event.delta.text };
                }
              } else if (event.type === 'content_block_start') {
                if (event.content_block?.type === 'tool_use') {
                  yield {
                    type: 'tool_use',
                    toolName: event.content_block.name,
                  };
                }
              } else if (event.type === 'message_stop') {
                yield { type: 'done' };
              }
            } catch {
              // Skip malformed JSON
            }
          }
        }
      }

      yield { type: 'done' };
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      yield { type: 'error', error: message };
    }
  }

  /**
   * Send a message to Claude and get a complete response.
   */
  async complete(
    messages: Message[],
    options?: {
      model?: string;
      maxTokens?: number;
      system?: string;
    }
  ): Promise<ClaudeResponse> {
    const model = options?.model ?? 'claude-sonnet-4-20250514';
    const maxTokens = options?.maxTokens ?? 4096;

    const response = await fetch(this.getUrl(), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': this.apiKey,
        'anthropic-version': '2023-06-01',
        'anthropic-dangerous-direct-browser-access': 'true',
      },
      body: JSON.stringify({
        model,
        max_tokens: maxTokens,
        system: options?.system,
        messages,
      }),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`API error: ${response.status} - ${error}`);
    }

    const data = await response.json();

    // Extract text content
    const textContent = data.content.find((c: { type: string }) => c.type === 'text');
    const toolContent = data.content.find((c: { type: string }) => c.type === 'tool_use');

    return {
      content: textContent?.text ?? '',
      stopReason: data.stop_reason,
      toolUse: toolContent ? {
        name: toolContent.name,
        input: toolContent.input,
      } : undefined,
    };
  }
}

export default ClaudeClient;
