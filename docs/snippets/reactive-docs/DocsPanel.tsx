import type { TutorialState, TutorialStep } from './types';

interface DocsPanelProps {
  /** Current tutorial state */
  state: TutorialState;
  /** Called when user clicks [Show me] */
  onShowMe: () => void;
  /** Called when user clicks Skip */
  onSkip: () => void;
  /** Called when user clicks Reset */
  onReset: () => void;
}

/**
 * Documentation panel that displays tutorial steps and [Show me] buttons.
 * Updates reactively based on terminal activity.
 */
export function DocsPanel({
  state,
  onShowMe,
  onSkip,
  onReset,
}: DocsPanelProps) {
  const { tutorial, currentStepIndex, isExecuting, isComplete } = state;
  const currentStep = tutorial.steps[currentStepIndex];

  if (isComplete) {
    return (
      <div style={styles.container}>
        <div style={styles.complete}>
          <div style={styles.completeIcon}>✓</div>
          <h2 style={styles.completeTitle}>Tutorial Complete!</h2>
          <p style={styles.completeText}>
            You've completed the {tutorial.name} tutorial.
          </p>
          <button onClick={onReset} style={styles.resetButton}>
            Start Over
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      {/* Progress indicator */}
      <div style={styles.progress}>
        <div style={styles.progressText}>
          Step {currentStepIndex + 1} of {tutorial.steps.length}
        </div>
        <div style={styles.progressBar}>
          <div
            style={{
              ...styles.progressFill,
              width: `${((currentStepIndex + 1) / tutorial.steps.length) * 100}%`,
            }}
          />
        </div>
      </div>

      {/* Current step */}
      <div style={styles.step}>
        <h2 style={styles.stepTitle}>{currentStep.title}</h2>
        <p style={styles.stepDescription}>{currentStep.description}</p>

        {/* Show command preview if available */}
        {currentStep.command && !currentStep.requiresUserAction && (
          <div style={styles.commandPreview}>
            <code style={styles.commandCode}>{currentStep.command}</code>
          </div>
        )}

        {/* Action buttons */}
        <div style={styles.actions}>
          {!currentStep.requiresUserAction && currentStep.command && (
            <button
              onClick={onShowMe}
              disabled={isExecuting}
              style={{
                ...styles.showMeButton,
                opacity: isExecuting ? 0.7 : 1,
                cursor: isExecuting ? 'not-allowed' : 'pointer',
              }}
            >
              {isExecuting
                ? currentStep.runningLabel || 'Running...'
                : currentStep.showMeLabel || 'Show me'}
            </button>
          )}

          {currentStep.requiresUserAction && (
            <div style={styles.waitingMessage}>
              Waiting for you to complete this step in the terminal...
            </div>
          )}

          <button onClick={onSkip} style={styles.skipButton} disabled={isExecuting}>
            Skip
          </button>
        </div>

        {/* Hint */}
        {currentStep.hint && (
          <div style={styles.hint}>
            <span style={styles.hintLabel}>Hint:</span> {currentStep.hint}
          </div>
        )}
      </div>

      {/* Step list preview */}
      <div style={styles.stepList}>
        {tutorial.steps.map((step, index) => (
          <StepIndicator
            key={step.id}
            step={step}
            index={index}
            currentIndex={currentStepIndex}
          />
        ))}
      </div>
    </div>
  );
}

function StepIndicator({
  step,
  index,
  currentIndex,
}: {
  step: TutorialStep;
  index: number;
  currentIndex: number;
}) {
  const isComplete = index < currentIndex;
  const isCurrent = index === currentIndex;

  return (
    <div
      style={{
        ...styles.stepIndicator,
        opacity: isComplete || isCurrent ? 1 : 0.5,
      }}
    >
      <div
        style={{
          ...styles.stepDot,
          background: isComplete ? '#10b981' : isCurrent ? '#8B7355' : '#d1d5db',
        }}
      >
        {isComplete && <span style={{ fontSize: '10px' }}>✓</span>}
      </div>
      <span
        style={{
          ...styles.stepLabel,
          fontWeight: isCurrent ? 600 : 400,
        }}
      >
        {step.title}
      </span>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
    padding: '24px',
    background: '#fafafa',
    overflowY: 'auto',
  },
  progress: {
    marginBottom: '24px',
  },
  progressText: {
    fontSize: '13px',
    color: '#6b7280',
    marginBottom: '8px',
  },
  progressBar: {
    height: '4px',
    background: '#e5e7eb',
    borderRadius: '2px',
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    background: '#8B7355',
    transition: 'width 0.3s ease',
  },
  step: {
    flex: 1,
  },
  stepTitle: {
    fontSize: '24px',
    fontWeight: 600,
    color: '#111827',
    marginBottom: '12px',
    fontFamily: "'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
  },
  stepDescription: {
    fontSize: '16px',
    lineHeight: 1.6,
    color: '#374151',
    marginBottom: '20px',
  },
  commandPreview: {
    background: '#1a1a1a',
    padding: '12px 16px',
    borderRadius: '8px',
    marginBottom: '20px',
  },
  commandCode: {
    fontFamily: 'Menlo, Monaco, "Courier New", monospace',
    fontSize: '14px',
    color: '#d4d4d4',
  },
  actions: {
    display: 'flex',
    gap: '12px',
    alignItems: 'center',
    marginBottom: '20px',
  },
  showMeButton: {
    padding: '12px 24px',
    background: '#8B7355',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '16px',
    fontWeight: 500,
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  skipButton: {
    padding: '12px 20px',
    background: 'transparent',
    color: '#6b7280',
    border: '1px solid #d1d5db',
    borderRadius: '8px',
    fontSize: '14px',
    cursor: 'pointer',
  },
  waitingMessage: {
    padding: '12px 16px',
    background: '#fef3c7',
    color: '#92400e',
    borderRadius: '8px',
    fontSize: '14px',
  },
  hint: {
    padding: '12px 16px',
    background: '#eff6ff',
    borderRadius: '8px',
    fontSize: '14px',
    color: '#1e40af',
  },
  hintLabel: {
    fontWeight: 600,
  },
  stepList: {
    marginTop: 'auto',
    paddingTop: '24px',
    borderTop: '1px solid #e5e7eb',
  },
  stepIndicator: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '8px 0',
  },
  stepDot: {
    width: '20px',
    height: '20px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: 'white',
    fontSize: '12px',
    flexShrink: 0,
  },
  stepLabel: {
    fontSize: '14px',
    color: '#374151',
  },
  complete: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    textAlign: 'center',
  },
  completeIcon: {
    width: '64px',
    height: '64px',
    borderRadius: '50%',
    background: '#10b981',
    color: 'white',
    fontSize: '32px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: '24px',
  },
  completeTitle: {
    fontSize: '28px',
    fontWeight: 600,
    color: '#111827',
    marginBottom: '12px',
    fontFamily: "'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
  },
  completeText: {
    fontSize: '16px',
    color: '#6b7280',
    marginBottom: '24px',
  },
  resetButton: {
    padding: '12px 24px',
    background: '#8B7355',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '16px',
    fontWeight: 500,
    cursor: 'pointer',
  },
};

export default DocsPanel;
