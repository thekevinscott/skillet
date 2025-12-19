import { useState, useCallback, useRef, useEffect } from 'react';
import { Terminal } from './Terminal';
import {
  BackendRegistry,
  ClaudeBackend,
  LocalLLMBackend,
  AVAILABLE_MODELS,
  type LLMBackend,
  type LLMBackendStatus,
  type Message,
  type ModelId,
} from './llm';

interface UnifiedTerminalProps {
  /** Files to mount in the container */
  files?: Record<string, string>;
  /** Height of the terminal */
  height?: string;
  /** System prompt for the LLM */
  systemPrompt?: string;
  /** Default backend to use */
  defaultBackend?: 'claude' | 'local';
}

/**
 * Unified terminal with multiple LLM backend support.
 *
 * Features:
 * - Seamless switching between Claude API and local WebLLM
 * - Shared conversation history across backends
 * - Clear backend indicator
 * - Per-backend configuration UI
 *
 * Usage in MDX:
 * ```mdx
 * <UnifiedTerminal
 *   files={{ 'example.py': 'print("hello")' }}
 *   systemPrompt="You are a coding assistant."
 * />
 * ```
 */
export function UnifiedTerminal({
  files = {},
  height = '400px',
  systemPrompt,
  defaultBackend = 'local',
}: UnifiedTerminalProps) {
  // Registry and backends
  const registryRef = useRef<BackendRegistry | null>(null);
  const claudeBackendRef = useRef<ClaudeBackend | null>(null);
  const localBackendRef = useRef<LocalLLMBackend | null>(null);

  // State
  const [activeBackendId, setActiveBackendId] = useState<string>(defaultBackend);
  const [backendStatuses, setBackendStatuses] = useState<Record<string, LLMBackendStatus>>({});
  const [isProcessing, setIsProcessing] = useState(false);
  const [apiKey, setApiKey] = useState<string>('');
  const [selectedModel, setSelectedModel] = useState<ModelId>('Phi-3.5-mini-instruct-q4f16_1-MLC');
  const [showApiKeyInput, setShowApiKeyInput] = useState(false);

  const conversationRef = useRef<Message[]>([]);

  // Initialize backends
  useEffect(() => {
    const registry = new BackendRegistry();
    const claudeBackend = new ClaudeBackend();
    const localBackend = new LocalLLMBackend();

    registry.register(claudeBackend);
    registry.register(localBackend);

    registryRef.current = registry;
    claudeBackendRef.current = claudeBackend;
    localBackendRef.current = localBackend;

    // Check initial statuses
    const checkStatuses = async () => {
      await localBackend.isAvailable();
      setBackendStatuses({
        claude: claudeBackend.getStatus(),
        local: localBackend.getStatus(),
      });
    };

    checkStatuses();

    // Subscribe to status changes
    const unsubscribe = registry.onStatusChange((backendId, status) => {
      setBackendStatuses((prev) => ({ ...prev, [backendId]: status }));
    });

    // Load saved API key
    if (typeof window !== 'undefined') {
      const savedKey = localStorage.getItem('anthropic_api_key');
      if (savedKey) {
        setApiKey(savedKey);
      }
    }

    return unsubscribe;
  }, []);

  // Handle API key change
  const handleApiKeyChange = useCallback((key: string) => {
    setApiKey(key);
    if (claudeBackendRef.current) {
      claudeBackendRef.current.setApiKey(key || null);
      setBackendStatuses((prev) => ({
        ...prev,
        claude: claudeBackendRef.current!.getStatus(),
      }));
    }
  }, []);

  // Handle model selection
  const handleModelChange = useCallback((modelId: ModelId) => {
    setSelectedModel(modelId);
    if (localBackendRef.current) {
      localBackendRef.current.setModel(modelId);
      setBackendStatuses((prev) => ({
        ...prev,
        local: localBackendRef.current!.getStatus(),
      }));
    }
  }, []);

  // Load local model
  const handleLoadModel = useCallback(async () => {
    if (!localBackendRef.current) return;

    try {
      await localBackendRef.current.initialize();
    } catch (err) {
      // Error is reflected in status
    }
  }, []);

  // Switch backend
  const handleBackendSwitch = useCallback((backendId: string) => {
    setActiveBackendId(backendId);
    if (backendId === 'claude') {
      setShowApiKeyInput(true);
    }
  }, []);

  // Handle LLM command
  const handleLLMCommand = useCallback(
    async (prompt: string, writeOutput: (text: string) => void) => {
      let backend: LLMBackend | null = null;

      if (activeBackendId === 'claude') {
        backend = claudeBackendRef.current;
      } else if (activeBackendId === 'local') {
        backend = localBackendRef.current;
      }

      if (!backend) {
        writeOutput('\r\n\x1b[31mError: No backend available\x1b[0m\r\n');
        return;
      }

      const status = backend.getStatus();
      if (status.state !== 'active') {
        writeOutput(`\r\n\x1b[31mError: Backend not ready (${status.message || status.state})\x1b[0m\r\n`);
        return;
      }

      setIsProcessing(true);
      conversationRef.current.push({ role: 'user', content: prompt });

      try {
        const backendLabel = activeBackendId === 'claude' ? 'Claude' : 'Local LLM';
        writeOutput(`\r\n\x1b[36m${backendLabel}:\x1b[0m `);

        let fullResponse = '';

        for await (const event of backend.stream(conversationRef.current, {
          system: systemPrompt,
        })) {
          if (event.type === 'text' && event.text) {
            const text = event.text.replace(/\n/g, '\r\n');
            writeOutput(text);
            fullResponse += event.text;
          } else if (event.type === 'error') {
            writeOutput(`\r\n\x1b[31mError: ${event.error}\x1b[0m\r\n`);
          }
        }

        if (fullResponse) {
          conversationRef.current.push({ role: 'assistant', content: fullResponse });
        }

        writeOutput('\r\n');
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error';
        writeOutput(`\r\n\x1b[31mError: ${message}\x1b[0m\r\n`);
      } finally {
        setIsProcessing(false);
      }
    },
    [activeBackendId, systemPrompt]
  );

  // Command handler for terminal
  const commandHandler = useCallback(
    (command: string, writeOutput: (text: string) => void): boolean => {
      const trimmed = command.trim();

      // Check for ai/llm/claude commands
      const prefixes = ['ai ', 'llm ', 'claude ', '@ai ', '@llm ', '@claude '];
      for (const prefix of prefixes) {
        if (trimmed.startsWith(prefix)) {
          const prompt = trimmed.slice(prefix.length).trim();
          if (prompt) {
            handleLLMCommand(prompt, writeOutput);
            return true;
          }
        }
      }

      return false;
    },
    [handleLLMCommand]
  );

  const claudeStatus = backendStatuses.claude || { state: 'ready' };
  const localStatus = backendStatuses.local || { state: 'ready' };
  const isClaudeActive = activeBackendId === 'claude' && claudeStatus.state === 'active';
  const isLocalActive = activeBackendId === 'local' && localStatus.state === 'active';

  return (
    <div>
      {/* Backend selector */}
      <div
        style={{
          display: 'flex',
          gap: '8px',
          marginBottom: '12px',
          flexWrap: 'wrap',
        }}
      >
        {/* Claude backend button */}
        <button
          onClick={() => handleBackendSwitch('claude')}
          style={{
            padding: '8px 16px',
            background: activeBackendId === 'claude' ? '#8B7355' : '#f3f4f6',
            color: activeBackendId === 'claude' ? 'white' : '#374151',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '14px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          {isClaudeActive && <span style={{ color: '#10b981' }}>●</span>}
          Claude API
        </button>

        {/* Local LLM backend button */}
        <button
          onClick={() => handleBackendSwitch('local')}
          disabled={localStatus.state === 'unavailable'}
          style={{
            padding: '8px 16px',
            background: activeBackendId === 'local' ? '#8B7355' : '#f3f4f6',
            color: activeBackendId === 'local' ? 'white' : '#374151',
            border: 'none',
            borderRadius: '6px',
            cursor: localStatus.state === 'unavailable' ? 'not-allowed' : 'pointer',
            fontSize: '14px',
            opacity: localStatus.state === 'unavailable' ? 0.5 : 1,
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          {isLocalActive && <span style={{ color: '#10b981' }}>●</span>}
          Local LLM
        </button>

        {/* Conversation indicator */}
        {conversationRef.current.length > 0 && (
          <span
            style={{
              padding: '8px 12px',
              fontSize: '13px',
              color: '#6b7280',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
            }}
          >
            {conversationRef.current.length} messages
          </span>
        )}
      </div>

      {/* Claude configuration */}
      {activeBackendId === 'claude' && (showApiKeyInput || !isClaudeActive) && (
        <div
          style={{
            padding: '12px 16px',
            background: '#fef3c7',
            borderRadius: '8px',
            marginBottom: '12px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => handleApiKeyChange(e.target.value)}
              placeholder="Enter Anthropic API key"
              style={{
                flex: 1,
                minWidth: '200px',
                padding: '8px 12px',
                borderRadius: '6px',
                border: '1px solid #d1d5db',
                fontSize: '14px',
              }}
            />
            {apiKey && (
              <button
                onClick={() => setShowApiKeyInput(false)}
                style={{
                  padding: '8px 16px',
                  background: '#10b981',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '14px',
                }}
              >
                Save
              </button>
            )}
          </div>
          <p style={{ margin: '8px 0 0', fontSize: '12px', color: '#92400e' }}>
            Your key is stored locally in your browser. Never sent to our servers.
          </p>
        </div>
      )}

      {/* Local LLM configuration */}
      {activeBackendId === 'local' && localStatus.state !== 'unavailable' && (
        <>
          {localStatus.state === 'ready' && (
            <div
              style={{
                padding: '12px 16px',
                background: '#f0fdf4',
                borderRadius: '8px',
                marginBottom: '12px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                <select
                  value={selectedModel}
                  onChange={(e) => handleModelChange(e.target.value as ModelId)}
                  style={{
                    padding: '6px 12px',
                    borderRadius: '6px',
                    border: '1px solid #d1d5db',
                    fontSize: '14px',
                  }}
                >
                  {AVAILABLE_MODELS.map((model) => (
                    <option key={model.id} value={model.id}>
                      {model.name} ({model.size})
                    </option>
                  ))}
                </select>
                <button
                  onClick={handleLoadModel}
                  style={{
                    padding: '8px 16px',
                    background: '#10b981',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '14px',
                  }}
                >
                  Load Model
                </button>
              </div>
              <p style={{ margin: '8px 0 0', fontSize: '12px', color: '#6b7280' }}>
                First load downloads the model (~1-2GB). It's cached for future visits.
              </p>
            </div>
          )}

          {localStatus.state === 'initializing' && (
            <div
              style={{
                padding: '16px',
                background: '#eff6ff',
                borderRadius: '8px',
                marginBottom: '12px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '14px', fontWeight: 500 }}>Loading model...</span>
                <span style={{ fontSize: '14px', color: '#6b7280' }}>
                  {Math.round((localStatus.progress ?? 0) * 100)}%
                </span>
              </div>
              <div
                style={{
                  height: '8px',
                  background: '#dbeafe',
                  borderRadius: '4px',
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    height: '100%',
                    width: `${(localStatus.progress ?? 0) * 100}%`,
                    background: '#3b82f6',
                    transition: 'width 0.3s',
                  }}
                />
              </div>
              <p style={{ margin: '8px 0 0', fontSize: '12px', color: '#6b7280' }}>
                {localStatus.message}
              </p>
            </div>
          )}

          {localStatus.state === 'error' && (
            <div
              style={{
                padding: '12px 16px',
                background: '#fef2f2',
                borderRadius: '8px',
                marginBottom: '12px',
                color: '#dc2626',
                fontSize: '14px',
              }}
            >
              Error: {localStatus.message}
            </div>
          )}
        </>
      )}

      {/* WebGPU not supported */}
      {activeBackendId === 'local' && localStatus.state === 'unavailable' && (
        <div
          style={{
            padding: '16px',
            background: '#fef3c7',
            borderRadius: '8px',
            marginBottom: '12px',
            color: '#92400e',
          }}
        >
          <strong>WebGPU not supported</strong>
          <p style={{ margin: '8px 0 0', fontSize: '14px' }}>
            Your browser doesn't support WebGPU. Try Chrome 113+ or Edge 113+, or use Claude API
            instead.
          </p>
        </div>
      )}

      {/* Active backend indicator */}
      {(isClaudeActive || isLocalActive) && (
        <div
          style={{
            padding: '8px 12px',
            background: '#dcfce7',
            borderRadius: '8px',
            marginBottom: '12px',
            fontSize: '14px',
            color: '#166534',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <span>●</span>
          <span>
            {isClaudeActive ? 'Claude' : 'Local LLM'} ready! Use{' '}
            <code style={{ background: '#bbf7d0', padding: '2px 4px', borderRadius: '4px' }}>
              ai &lt;prompt&gt;
            </code>{' '}
            in the terminal.
          </span>
        </div>
      )}

      {/* Processing indicator */}
      {isProcessing && (
        <div
          style={{
            padding: '8px 12px',
            background: '#dbeafe',
            borderRadius: '8px',
            marginBottom: '12px',
            fontSize: '14px',
            color: '#1e40af',
          }}
        >
          {activeBackendId === 'claude' ? 'Claude' : 'Local LLM'} is thinking...
        </div>
      )}

      <Terminal
        files={files}
        height={height}
        commandHandler={isClaudeActive || isLocalActive ? commandHandler : undefined}
      />
    </div>
  );
}

export default UnifiedTerminal;
