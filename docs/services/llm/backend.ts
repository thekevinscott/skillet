/**
 * Unified LLM backend interface.
 * Abstracts over different LLM providers (Claude API, local WebLLM, etc.)
 */

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

export interface LLMBackendStatus {
  state: 'unavailable' | 'ready' | 'initializing' | 'active' | 'error';
  message?: string;
  progress?: number;
}

/**
 * Common interface for all LLM backends.
 */
export interface LLMBackend {
  /** Unique identifier for this backend */
  readonly id: string;

  /** Human-readable name */
  readonly name: string;

  /** Short description */
  readonly description: string;

  /** Check if this backend is available in the current environment */
  isAvailable(): Promise<boolean>;

  /** Get current status */
  getStatus(): LLMBackendStatus;

  /** Initialize the backend (load models, etc.) */
  initialize(): Promise<void>;

  /** Stream a chat completion */
  stream(
    messages: Message[],
    options?: { system?: string }
  ): AsyncGenerator<StreamEvent>;

  /** Subscribe to status changes */
  onStatusChange(callback: (status: LLMBackendStatus) => void): () => void;
}

/**
 * Backend registry for managing multiple LLM backends.
 */
export class BackendRegistry {
  private backends: Map<string, LLMBackend> = new Map();
  private activeBackendId: string | null = null;
  private conversationHistory: Message[] = [];
  private statusListeners: Set<(backendId: string, status: LLMBackendStatus) => void> = new Set();

  /**
   * Register a backend.
   */
  register(backend: LLMBackend): void {
    this.backends.set(backend.id, backend);

    // Subscribe to status changes
    backend.onStatusChange((status) => {
      this.notifyStatusListeners(backend.id, status);
    });
  }

  /**
   * Get all registered backends.
   */
  getAll(): LLMBackend[] {
    return Array.from(this.backends.values());
  }

  /**
   * Get a specific backend by ID.
   */
  get(id: string): LLMBackend | undefined {
    return this.backends.get(id);
  }

  /**
   * Get the active backend.
   */
  getActive(): LLMBackend | null {
    if (!this.activeBackendId) return null;
    return this.backends.get(this.activeBackendId) ?? null;
  }

  /**
   * Set the active backend.
   */
  async setActive(id: string): Promise<void> {
    const backend = this.backends.get(id);
    if (!backend) {
      throw new Error(`Backend '${id}' not found`);
    }

    const status = backend.getStatus();
    if (status.state === 'unavailable') {
      throw new Error(`Backend '${id}' is not available`);
    }

    if (status.state === 'ready') {
      await backend.initialize();
    }

    this.activeBackendId = id;
  }

  /**
   * Get the conversation history (shared across backends).
   */
  getConversation(): Message[] {
    return [...this.conversationHistory];
  }

  /**
   * Add a message to the conversation.
   */
  addMessage(message: Message): void {
    this.conversationHistory.push(message);
  }

  /**
   * Clear the conversation history.
   */
  clearConversation(): void {
    this.conversationHistory = [];
  }

  /**
   * Subscribe to backend status changes.
   */
  onStatusChange(callback: (backendId: string, status: LLMBackendStatus) => void): () => void {
    this.statusListeners.add(callback);
    return () => this.statusListeners.delete(callback);
  }

  private notifyStatusListeners(backendId: string, status: LLMBackendStatus): void {
    for (const listener of this.statusListeners) {
      listener(backendId, status);
    }
  }
}

export default BackendRegistry;
