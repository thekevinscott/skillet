import { useReducer, useRef, useCallback, useEffect, useState } from 'react';
import { Terminal, type TerminalRef } from '../Terminal';
import { DocsPanel } from './DocsPanel';
import {
  type Tutorial,
  type TutorialState,
  tutorialReducer,
  createInitialState,
} from './types';

interface ReactiveDocsLayoutProps {
  /** The tutorial to run */
  tutorial: Tutorial;
  /** Height of the entire layout */
  height?: string;
  /** Custom command handler for the terminal */
  commandHandler?: (command: string, writeOutput: (text: string) => void) => boolean;
}

/**
 * Reactive documentation layout with split-pane view.
 *
 * Features:
 * - Docs panel on the left with tutorial steps
 * - Terminal on the right with WebContainer
 * - [Show me] buttons that execute commands with typing animation
 * - Auto-advance when terminal output matches expected patterns
 *
 * Usage in MDX:
 * ```mdx
 * <ReactiveDocsLayout tutorial={commitMessageTutorial} />
 * ```
 */
export function ReactiveDocsLayout({
  tutorial,
  height = '600px',
  commandHandler,
}: ReactiveDocsLayoutProps) {
  const terminalRef = useRef<TerminalRef>(null);
  const [state, dispatch] = useReducer(tutorialReducer, createInitialState(tutorial));
  const [isTerminalReady, setIsTerminalReady] = useState(false);

  // Track output for pattern matching
  const outputBufferRef = useRef<string>('');
  const advanceTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Handle terminal output
  const handleOutput = useCallback((data: string) => {
    outputBufferRef.current += data;
    dispatch({ type: 'OUTPUT', data });

    // Check if we should auto-advance
    const currentStep = state.tutorial.steps[state.currentStepIndex];
    if (currentStep && state.isExecuting) {
      const shouldAdvance =
        (currentStep.watchPattern && currentStep.watchPattern.test(outputBufferRef.current)) ||
        (currentStep.validate && currentStep.validate(outputBufferRef.current));

      if (shouldAdvance) {
        // Clear any existing timeout
        if (advanceTimeoutRef.current) {
          clearTimeout(advanceTimeoutRef.current);
        }
        // Advance after a short delay to let output settle
        advanceTimeoutRef.current = setTimeout(() => {
          dispatch({ type: 'ADVANCE' });
          outputBufferRef.current = '';
        }, 1000);
      }
    }
  }, [state.tutorial.steps, state.currentStepIndex, state.isExecuting]);

  // Handle [Show me] click
  const handleShowMe = useCallback(async () => {
    const currentStep = state.tutorial.steps[state.currentStepIndex];
    if (!currentStep?.command || !terminalRef.current?.isReady()) return;

    dispatch({ type: 'EXECUTE_START' });
    outputBufferRef.current = '';

    try {
      // Execute the command with typing animation
      await terminalRef.current.executeCommand(currentStep.command);

      // If no watch pattern, advance after a delay
      if (!currentStep.watchPattern && !currentStep.validate) {
        setTimeout(() => {
          dispatch({ type: 'ADVANCE' });
        }, 1500);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Command failed';
      dispatch({ type: 'ERROR', message });
    }
  }, [state.tutorial.steps, state.currentStepIndex]);

  // Handle skip
  const handleSkip = useCallback(() => {
    dispatch({ type: 'SKIP' });
    outputBufferRef.current = '';
  }, []);

  // Handle reset
  const handleReset = useCallback(() => {
    dispatch({ type: 'RESET' });
    outputBufferRef.current = '';
  }, []);

  // Handle terminal ready
  const handleTerminalReady = useCallback(() => {
    setIsTerminalReady(true);
  }, []);

  // Cleanup timeouts on unmount
  useEffect(() => {
    return () => {
      if (advanceTimeoutRef.current) {
        clearTimeout(advanceTimeoutRef.current);
      }
    };
  }, []);

  return (
    <div style={{ ...styles.container, height }}>
      {/* Docs Panel (left) */}
      <div style={styles.docsPane}>
        <DocsPanel
          state={state}
          onShowMe={handleShowMe}
          onSkip={handleSkip}
          onReset={handleReset}
        />
      </div>

      {/* Divider */}
      <div style={styles.divider} />

      {/* Terminal (right) */}
      <div style={styles.terminalPane}>
        {!isTerminalReady && (
          <div style={styles.terminalLoading}>
            <div style={styles.spinner} />
            <span>Initializing terminal...</span>
          </div>
        )}
        <Terminal
          ref={terminalRef}
          files={tutorial.files}
          height="100%"
          onReady={handleTerminalReady}
          onOutput={handleOutput}
          commandHandler={commandHandler}
        />
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    borderRadius: '12px',
    overflow: 'hidden',
    border: '1px solid #e5e7eb',
    background: '#ffffff',
  },
  docsPane: {
    width: '40%',
    minWidth: '300px',
    maxWidth: '500px',
    borderRight: '1px solid #e5e7eb',
  },
  divider: {
    width: '1px',
    background: '#e5e7eb',
  },
  terminalPane: {
    flex: 1,
    position: 'relative',
    minWidth: '400px',
  },
  terminalLoading: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    background: '#1a1a1a',
    color: '#d4d4d4',
    gap: '12px',
    zIndex: 10,
  },
  spinner: {
    width: '24px',
    height: '24px',
    border: '3px solid #333',
    borderTopColor: '#8B7355',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  },
};

// Add keyframes for spinner
if (typeof document !== 'undefined') {
  const styleSheet = document.createElement('style');
  styleSheet.textContent = `
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
  `;
  document.head.appendChild(styleSheet);
}

export default ReactiveDocsLayout;
