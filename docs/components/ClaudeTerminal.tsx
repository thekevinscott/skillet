import { useState, useCallback, useRef } from 'react';
import { Terminal } from './Terminal';
import { ApiKeyInput } from './ApiKeyInput';
import { ClaudeClient, StreamEvent } from './claude';

interface ClaudeTerminalProps {
  /** Files to mount in the container */
  files?: Record<string, string>;
  /** Height of the terminal */
  height?: string;
  /** System prompt for Claude */
  systemPrompt?: string;
}

/**
 * Terminal with integrated Claude AI assistant.
 *
 * Usage in MDX:
 * ```mdx
 * <ClaudeTerminal
 *   files={{ 'bug.py': 'def add(a, b):\n  return a - b' }}
 *   systemPrompt="You are helping debug Python code."
 * />
 * ```
 */
export function ClaudeTerminal({
  files = {},
  height = '400px',
  systemPrompt,
}: ClaudeTerminalProps) {
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const clientRef = useRef<ClaudeClient | null>(null);
  const conversationRef = useRef<Array<{ role: 'user' | 'assistant'; content: string }>>([]);

  // Update client when API key changes
  const handleKeyChange = useCallback((key: string | null) => {
    setApiKey(key);
    if (key) {
      clientRef.current = new ClaudeClient(key);
    } else {
      clientRef.current = null;
    }
  }, []);

  // Handle Claude command
  const handleClaudeCommand = useCallback(async (
    prompt: string,
    writeOutput: (text: string) => void
  ) => {
    if (!clientRef.current) {
      writeOutput('\r\n\x1b[31mError: No API key configured\x1b[0m\r\n');
      return;
    }

    setIsProcessing(true);

    // Add user message to conversation
    conversationRef.current.push({ role: 'user', content: prompt });

    try {
      writeOutput('\r\n\x1b[36mClaude:\x1b[0m ');

      let fullResponse = '';

      for await (const event of clientRef.current.stream(
        conversationRef.current,
        { system: systemPrompt }
      )) {
        if (event.type === 'text' && event.text) {
          // Handle newlines for terminal display
          const text = event.text.replace(/\n/g, '\r\n');
          writeOutput(text);
          fullResponse += event.text;
        } else if (event.type === 'error') {
          writeOutput(`\r\n\x1b[31mError: ${event.error}\x1b[0m\r\n`);
        }
      }

      // Add assistant response to conversation
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
  }, [systemPrompt]);

  // Custom command handler that intercepts 'claude' commands
  const commandHandler = useCallback((
    command: string,
    writeOutput: (text: string) => void
  ): boolean => {
    const trimmed = command.trim();

    // Check if this is a claude command
    if (trimmed.startsWith('claude ')) {
      const prompt = trimmed.slice(7).trim();
      if (prompt) {
        handleClaudeCommand(prompt, writeOutput);
        return true; // Command handled
      }
    }

    // Check for shorthand @claude
    if (trimmed.startsWith('@claude ')) {
      const prompt = trimmed.slice(8).trim();
      if (prompt) {
        handleClaudeCommand(prompt, writeOutput);
        return true;
      }
    }

    return false; // Let terminal handle normally
  }, [handleClaudeCommand]);

  return (
    <div>
      <ApiKeyInput onKeyChange={handleKeyChange} />

      {!apiKey && (
        <div style={{
          padding: '12px',
          background: '#fef3c7',
          borderRadius: '8px',
          marginBottom: '12px',
          fontSize: '14px',
          color: '#92400e',
        }}>
          Enter your Anthropic API key above to enable Claude commands.
          Use <code style={{ background: '#fde68a', padding: '2px 4px', borderRadius: '4px' }}>claude &lt;prompt&gt;</code> or <code style={{ background: '#fde68a', padding: '2px 4px', borderRadius: '4px' }}>@claude &lt;prompt&gt;</code> in the terminal.
        </div>
      )}

      {isProcessing && (
        <div style={{
          padding: '8px 12px',
          background: '#dbeafe',
          borderRadius: '8px',
          marginBottom: '12px',
          fontSize: '14px',
          color: '#1e40af',
        }}>
          Claude is thinking...
        </div>
      )}

      <Terminal
        files={files}
        height={height}
        commandHandler={commandHandler}
      />
    </div>
  );
}

export default ClaudeTerminal;
