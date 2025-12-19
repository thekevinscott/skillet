import { useEffect, useRef, useState, useCallback, forwardRef, useImperativeHandle } from 'react';
import { Terminal as XTerm } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import { WebContainer } from '@webcontainer/api';
import '@xterm/xterm/css/xterm.css';

/** Methods exposed by Terminal ref */
export interface TerminalRef {
  /** Execute a command with typing animation */
  executeCommand: (command: string, delay?: number) => Promise<void>;
  /** Type text character by character */
  typeText: (text: string, delay?: number) => Promise<void>;
  /** Write text directly to terminal (no animation) */
  write: (text: string) => void;
  /** Check if terminal is ready */
  isReady: () => boolean;
}

interface TerminalProps {
  /** Initial commands to run on boot */
  initialCommands?: string[];
  /** Files to mount in the container */
  files?: Record<string, string>;
  /** Height of the terminal */
  height?: string;
  /** Called when terminal is ready */
  onReady?: () => void;
  /** Custom command handler - return true if handled, false to pass to shell */
  commandHandler?: (command: string, writeOutput: (text: string) => void) => boolean;
  /** Called when terminal output is received */
  onOutput?: (data: string) => void;
}

type TerminalStatus = 'booting' | 'ready' | 'error';

/**
 * Interactive terminal component with WebContainer sandboxed execution.
 *
 * Usage in MDX:
 * ```mdx
 * <Terminal
 *   files={{ 'hello.txt': 'Hello World!' }}
 *   initialCommands={['cat hello.txt']}
 * />
 * ```
 *
 * With ref for programmatic control:
 * ```tsx
 * const terminalRef = useRef<TerminalRef>(null);
 * <Terminal ref={terminalRef} />
 * // Later: terminalRef.current?.executeCommand('ls -la');
 * ```
 */
export const Terminal = forwardRef<TerminalRef, TerminalProps>(function Terminal({
  initialCommands = [],
  files = {},
  height = '400px',
  onReady,
  commandHandler,
  onOutput,
}, ref) {
  const terminalRef = useRef<HTMLDivElement>(null);
  const xtermRef = useRef<XTerm | null>(null);
  const containerRef = useRef<WebContainer | null>(null);
  const fitAddonRef = useRef<FitAddon | null>(null);
  const inputStreamRef = useRef<WritableStreamDefaultWriter | null>(null);
  const currentLineRef = useRef<string>('');

  const [status, setStatus] = useState<TerminalStatus>('booting');
  const [error, setError] = useState<string | null>(null);

  // Type text character by character (for [Show me] automation)
  const typeText = useCallback(async (text: string, delay = 50) => {
    if (!inputStreamRef.current) return;

    for (const char of text) {
      xtermRef.current?.write(char);
      await inputStreamRef.current.write(char);
      await sleep(delay);
    }
  }, []);

  // Execute a command with typing animation
  const executeCommand = useCallback(async (command: string, delay = 50) => {
    await typeText(command, delay);
    await typeText('\n', 0);
  }, [typeText]);

  // Write directly to terminal (no animation)
  const write = useCallback((text: string) => {
    xtermRef.current?.write(text);
  }, []);

  // Check if ready
  const isReady = useCallback(() => status === 'ready', [status]);

  // Expose methods via ref
  useImperativeHandle(ref, () => ({
    executeCommand,
    typeText,
    write,
    isReady,
  }), [executeCommand, typeText, write, isReady]);

  // Notify parent when ready
  useEffect(() => {
    if (status === 'ready' && onReady) {
      onReady();
    }
  }, [status, onReady]);

  useEffect(() => {
    if (!terminalRef.current) return;

    let mounted = true;

    const init = async () => {
      try {
        // Initialize xterm.js
        const xterm = new XTerm({
          cursorBlink: true,
          fontSize: 14,
          fontFamily: 'Menlo, Monaco, "Courier New", monospace',
          theme: {
            background: '#1a1a1a',
            foreground: '#d4d4d4',
            cursor: '#d4d4d4',
            cursorAccent: '#1a1a1a',
            selectionBackground: '#264f78',
          },
        });

        const fitAddon = new FitAddon();
        xterm.loadAddon(fitAddon);

        xterm.open(terminalRef.current!);
        fitAddon.fit();

        xtermRef.current = xterm;
        fitAddonRef.current = fitAddon;

        xterm.writeln('Booting WebContainer...\r\n');

        // Boot WebContainer
        const container = await WebContainer.boot();
        if (!mounted) return;

        containerRef.current = container;

        // Mount files
        if (Object.keys(files).length > 0) {
          const fileTree: Record<string, { file: { contents: string } }> = {};
          for (const [path, contents] of Object.entries(files)) {
            fileTree[path] = { file: { contents } };
          }
          await container.mount(fileTree);
        }

        // Start shell
        const shellProcess = await container.spawn('jsh', {
          terminal: { cols: xterm.cols, rows: xterm.rows },
        });

        // Connect shell output to terminal
        shellProcess.output.pipeTo(
          new WritableStream({
            write(data) {
              xterm.write(data);
              // Notify parent of output
              if (onOutput) {
                onOutput(data);
              }
            },
          })
        );

        // Connect terminal input to shell
        const inputWriter = shellProcess.input.getWriter();
        inputStreamRef.current = inputWriter;

        // Handle input with optional command interception
        xterm.onData((data) => {
          // Handle Enter key
          if (data === '\r') {
            const command = currentLineRef.current;
            currentLineRef.current = '';

            // Check if custom handler wants this command
            if (commandHandler && command.trim()) {
              const writeOutput = (text: string) => xterm.write(text);
              const handled = commandHandler(command, writeOutput);
              if (handled) {
                // Command was handled by custom handler
                xterm.write('\r\n');
                return;
              }
            }

            // Pass to shell
            inputWriter.write(data);
          }
          // Handle backspace
          else if (data === '\x7f') {
            if (currentLineRef.current.length > 0) {
              currentLineRef.current = currentLineRef.current.slice(0, -1);
              inputWriter.write(data);
            }
          }
          // Regular character
          else {
            currentLineRef.current += data;
            inputWriter.write(data);
          }
        });

        // Handle resize
        const resizeObserver = new ResizeObserver(() => {
          fitAddon.fit();
          shellProcess.resize({ cols: xterm.cols, rows: xterm.rows });
        });
        resizeObserver.observe(terminalRef.current!);

        setStatus('ready');

        // Run initial commands
        for (const cmd of initialCommands) {
          await sleep(500);
          await executeCommand(cmd);
        }

      } catch (err) {
        if (!mounted) return;
        const message = err instanceof Error ? err.message : 'Unknown error';
        setError(message);
        setStatus('error');
        xtermRef.current?.writeln(`\r\nError: ${message}`);
      }
    };

    init();

    return () => {
      mounted = false;
      xtermRef.current?.dispose();
    };
  }, [files, initialCommands, executeCommand]);

  // Handle window resize
  useEffect(() => {
    const handleResize = () => fitAddonRef.current?.fit();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <div className="terminal-wrapper" style={{ position: 'relative' }}>
      {status === 'booting' && (
        <div className="terminal-status" style={{
          position: 'absolute',
          top: '8px',
          right: '8px',
          padding: '4px 8px',
          background: '#3b82f6',
          color: 'white',
          borderRadius: '4px',
          fontSize: '12px',
          zIndex: 10,
        }}>
          Booting...
        </div>
      )}
      {status === 'error' && (
        <div className="terminal-error" style={{
          padding: '12px',
          background: '#fee2e2',
          color: '#dc2626',
          borderRadius: '4px',
          marginBottom: '8px',
        }}>
          {error}
        </div>
      )}
      <div
        ref={terminalRef}
        style={{
          height,
          borderRadius: '8px',
          overflow: 'hidden',
          background: '#1a1a1a',
        }}
      />
    </div>
  );
});

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export default Terminal;
