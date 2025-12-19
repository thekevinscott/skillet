/**
 * Types for the reactive docs tutorial system.
 */

/** A single step in a tutorial */
export interface TutorialStep {
  /** Unique ID for this step */
  id: string;
  /** Title shown in the docs panel */
  title: string;
  /** Description/explanation shown in the docs panel */
  description: string;
  /** Command to execute when [Show me] is clicked */
  command?: string;
  /** Text shown on the [Show me] button */
  showMeLabel?: string;
  /** Text shown while command is executing */
  runningLabel?: string;
  /** Pattern to watch for in terminal output to auto-advance */
  watchPattern?: RegExp;
  /** Custom validation function for terminal output */
  validate?: (output: string) => boolean;
  /** Whether this step requires user action (no [Show me] button) */
  requiresUserAction?: boolean;
  /** Hint shown if user is stuck */
  hint?: string;
}

/** A complete tutorial walkthrough */
export interface Tutorial {
  /** Unique ID for this tutorial */
  id: string;
  /** Display name */
  name: string;
  /** Short description */
  description: string;
  /** Files to pre-load in the terminal */
  files?: Record<string, string>;
  /** Tutorial steps in order */
  steps: TutorialStep[];
}

/** Current state of a tutorial */
export interface TutorialState {
  /** The tutorial being run */
  tutorial: Tutorial;
  /** Current step index */
  currentStepIndex: number;
  /** Whether the current step is executing */
  isExecuting: boolean;
  /** Accumulated terminal output for current step */
  outputBuffer: string;
  /** Whether the tutorial is complete */
  isComplete: boolean;
  /** Error message if something went wrong */
  error?: string;
}

/** Actions that can be dispatched to the tutorial state machine */
export type TutorialAction =
  | { type: 'START'; tutorial: Tutorial }
  | { type: 'SHOW_ME' }
  | { type: 'EXECUTE_START' }
  | { type: 'EXECUTE_COMPLETE' }
  | { type: 'OUTPUT'; data: string }
  | { type: 'ADVANCE' }
  | { type: 'SKIP' }
  | { type: 'RESET' }
  | { type: 'ERROR'; message: string };

/** Reducer for tutorial state */
export function tutorialReducer(
  state: TutorialState,
  action: TutorialAction
): TutorialState {
  switch (action.type) {
    case 'START':
      return {
        tutorial: action.tutorial,
        currentStepIndex: 0,
        isExecuting: false,
        outputBuffer: '',
        isComplete: false,
      };

    case 'EXECUTE_START':
      return {
        ...state,
        isExecuting: true,
        outputBuffer: '',
      };

    case 'EXECUTE_COMPLETE':
      return {
        ...state,
        isExecuting: false,
      };

    case 'OUTPUT': {
      const newBuffer = state.outputBuffer + action.data;
      const currentStep = state.tutorial.steps[state.currentStepIndex];

      // Check if output matches the watch pattern
      if (currentStep?.watchPattern?.test(newBuffer)) {
        // Auto-advance after a short delay (handled by caller)
        return { ...state, outputBuffer: newBuffer };
      }

      // Check custom validation
      if (currentStep?.validate?.(newBuffer)) {
        return { ...state, outputBuffer: newBuffer };
      }

      return { ...state, outputBuffer: newBuffer };
    }

    case 'ADVANCE': {
      const nextIndex = state.currentStepIndex + 1;
      if (nextIndex >= state.tutorial.steps.length) {
        return { ...state, isComplete: true, isExecuting: false };
      }
      return {
        ...state,
        currentStepIndex: nextIndex,
        isExecuting: false,
        outputBuffer: '',
      };
    }

    case 'SKIP':
      return {
        ...state,
        currentStepIndex: state.currentStepIndex + 1,
        isExecuting: false,
        outputBuffer: '',
        isComplete: state.currentStepIndex + 1 >= state.tutorial.steps.length,
      };

    case 'RESET':
      return {
        ...state,
        currentStepIndex: 0,
        isExecuting: false,
        outputBuffer: '',
        isComplete: false,
        error: undefined,
      };

    case 'ERROR':
      return {
        ...state,
        isExecuting: false,
        error: action.message,
      };

    default:
      return state;
  }
}

/** Create initial state for a tutorial */
export function createInitialState(tutorial: Tutorial): TutorialState {
  return {
    tutorial,
    currentStepIndex: 0,
    isExecuting: false,
    outputBuffer: '',
    isComplete: false,
  };
}
