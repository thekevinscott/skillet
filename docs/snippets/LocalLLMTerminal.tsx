import { useState, useCallback, useRef, useEffect } from 'react';
import { Terminal } from './Terminal';
import { LocalLLMClient, AVAILABLE_MODELS, type ModelId, type StreamEvent } from './webllm';

interface LocalLLMTerminalProps {
  /** Files to mount in the container */
  files?: Record<string, string>;
  /** Height of the terminal */
  height?: string;
  /** System prompt for the LLM */
  systemPrompt?: string;
  /** Default model to use */
  defaultModel?: ModelId;
}

type Status = 'checking' | 'unsupported' | 'ready' | 'loading' | 'loaded' | 'error';

/**
 * Terminal with integrated local LLM (WebLLM).
 * Runs entirely in the browser - no API key needed.
 *
 * Usage in MDX:
 * ```mdx
 * <LocalLLMTerminal
 *   files={{ 'example.py': 'print("hello")' }}
 *   systemPrompt="You are a coding assistant."
 * />
 * ```
 */
export function LocalLLMTerminal({
  files = {},
  height = '400px',
  systemPrompt,
  defaultModel = 'Phi-3.5-mini-instruct-q4f16_1-MLC',
}: LocalLLMTerminalProps) {
  const [status, setStatus] = useState<Status>('checking');
  const [selectedModel, setSelectedModel] = useState<ModelId>(defaultModel);
  const [loadProgress, setLoadProgress] = useState<{ text: string; progress: number } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const clientRef = useRef<LocalLLMClient | null>(null);
  const conversationRef = useRef<Array<{ role: 'user' | 'assistant'; content: string }>>([]);

  // Check WebGPU support on mount
  useEffect(() => {
    LocalLLMClient.isSupported().then((supported) => {
      setStatus(supported ? 'ready' : 'unsupported');
    });
  }, []);

  // Load the model
  const handleLoadModel = useCallback(async () => {
    setStatus('loading');
    setError(null);
    setLoadProgress({ text: 'Initializing...', progress: 0 });

    try {
      const client = new LocalLLMClient(selectedModel, {
        onProgress: setLoadProgress,
      });

      await client.initialize();
      clientRef.current = client;
      setStatus('loaded');
      setLoadProgress(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load model';
      setError(message);
      setStatus('error');
      setLoadProgress(null);
    }
  }, [selectedModel]);

  // Handle LLM command
  const handleLLMCommand = useCallback(
    async (prompt: string, writeOutput: (text: string) => void) => {
      if (!clientRef.current) {
        writeOutput('\r\n\x1b[31mError: Model not loaded\x1b[0m\r\n');
        return;
      }

      setIsProcessing(true);
      conversationRef.current.push({ role: 'user', content: prompt });

      try {
        writeOutput('\r\n\x1b[36mLocal LLM:\x1b[0m ');

        let fullResponse = '';

        for await (const event of clientRef.current.stream(conversationRef.current, {
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
    [systemPrompt]
  );

  // Command handler for terminal
  const commandHandler = useCallback(
    (command: string, writeOutput: (text: string) => void): boolean => {
      const trimmed = command.trim();

      // Check for llm/ai commands
      if (trimmed.startsWith('llm ') || trimmed.startsWith('ai ')) {
        const prompt = trimmed.slice(trimmed.indexOf(' ') + 1).trim();
        if (prompt) {
          handleLLMCommand(prompt, writeOutput);
          return true;
        }
      }

      // Check for @llm shorthand
      if (trimmed.startsWith('@llm ') || trimmed.startsWith('@ai ')) {
        const prompt = trimmed.slice(trimmed.indexOf(' ') + 1).trim();
        if (prompt) {
          handleLLMCommand(prompt, writeOutput);
          return true;
        }
      }

      return false;
    },
    [handleLLMCommand]
  );

  return (
    <div>
      {/* WebGPU not supported */}
      {status === 'unsupported' && (
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
            Your browser doesn't support WebGPU, which is required for local LLM inference. Try
            Chrome 113+ or Edge 113+.
          </p>
        </div>
      )}

      {/* Model selection and load button */}
      {(status === 'ready' || status === 'error') && (
        <div
          style={{
            padding: '12px 16px',
            background: '#f0fdf4',
            borderRadius: '8px',
            marginBottom: '12px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <label style={{ fontSize: '14px', fontWeight: 500 }}>
              Local LLM (no API key needed):
            </label>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value as ModelId)}
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
                padding: '6px 16px',
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
          {error && (
            <p style={{ margin: '8px 0 0', fontSize: '13px', color: '#dc2626' }}>{error}</p>
          )}
          <p style={{ margin: '8px 0 0', fontSize: '12px', color: '#6b7280' }}>
            First load downloads the model (~1-2GB). It's cached for future visits.
          </p>
        </div>
      )}

      {/* Loading progress */}
      {status === 'loading' && loadProgress && (
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
              {Math.round(loadProgress.progress * 100)}%
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
                width: `${loadProgress.progress * 100}%`,
                background: '#3b82f6',
                transition: 'width 0.3s',
              }}
            />
          </div>
          <p style={{ margin: '8px 0 0', fontSize: '12px', color: '#6b7280' }}>
            {loadProgress.text}
          </p>
        </div>
      )}

      {/* Model loaded */}
      {status === 'loaded' && (
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
          <span>✓</span>
          <span>
            Model loaded! Use{' '}
            <code style={{ background: '#bbf7d0', padding: '2px 4px', borderRadius: '4px' }}>
              llm &lt;prompt&gt;
            </code>{' '}
            or{' '}
            <code style={{ background: '#bbf7d0', padding: '2px 4px', borderRadius: '4px' }}>
              @ai &lt;prompt&gt;
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
          Local LLM is thinking...
        </div>
      )}

      <Terminal
        files={files}
        height={height}
        commandHandler={status === 'loaded' ? commandHandler : undefined}
      />
    </div>
  );
}

export default LocalLLMTerminal;
