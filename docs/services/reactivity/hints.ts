/**
 * Contextual hints service for reactive docs.
 * Provides helpful suggestions based on terminal output patterns.
 */

import { docsEventBus } from '../event-bus.js'
import type { PatternMatch } from './pattern-matcher.js'

export interface Hint {
  id: string
  message: string
  type: 'info' | 'warning' | 'error' | 'success'
  suggestion?: string
  action?: {
    label: string
    command: string
  }
  timeout?: number
}

export interface HintRule {
  pattern: RegExp | string
  hint: Omit<Hint, 'id'>
  /** Only trigger once per session */
  once?: boolean
  /** Minimum time since last hint (ms) */
  cooldown?: number
}

// Default contextual hints
export const defaultHintRules: HintRule[] = [
  // Help command hints
  {
    pattern: /--help|-h\s*$/m,
    hint: {
      message: 'Looking for help?',
      type: 'info',
      suggestion: 'Try running the command without flags to see basic usage',
      timeout: 5000,
    },
  },

  // Empty directory
  {
    pattern: /total 0/,
    hint: {
      message: 'This directory is empty',
      type: 'info',
      suggestion: 'You can create files with `touch filename` or `echo "content" > filename`',
      timeout: 5000,
    },
    once: true,
  },

  // Git init suggestion
  {
    pattern: /fatal: not a git repository/,
    hint: {
      message: 'Not a git repository',
      type: 'warning',
      suggestion: 'Initialize with `git init`',
      action: {
        label: 'Initialize Git',
        command: 'git init',
      },
    },
  },

  // npm install suggestion
  {
    pattern: /Cannot find module|MODULE_NOT_FOUND/,
    hint: {
      message: 'Missing dependencies',
      type: 'error',
      suggestion: 'Try running `npm install` to install dependencies',
      action: {
        label: 'Install Dependencies',
        command: 'npm install',
      },
    },
  },

  // Permission denied
  {
    pattern: /Permission denied|EACCES/i,
    hint: {
      message: 'Permission denied',
      type: 'error',
      suggestion: 'The file or command requires elevated permissions',
    },
  },

  // Command success patterns
  {
    pattern: /Successfully|completed|Done!/i,
    hint: {
      message: 'Command completed successfully!',
      type: 'success',
      timeout: 3000,
    },
    cooldown: 5000,
  },

  // Syntax errors
  {
    pattern: /SyntaxError|Unexpected token/,
    hint: {
      message: 'Syntax error detected',
      type: 'error',
      suggestion: 'Check for typos or missing brackets/quotes',
    },
  },

  // TypeScript errors
  {
    pattern: /error TS\d+:/,
    hint: {
      message: 'TypeScript compilation error',
      type: 'error',
      suggestion: 'Check the type annotations and imports',
    },
  },
]

export class HintsService {
  private rules: HintRule[] = []
  private triggeredOnce = new Set<string>()
  private lastHintTime = new Map<string, number>()
  private hintIdCounter = 0
  private activeHints = new Map<string, Hint>()

  constructor(rules: HintRule[] = defaultHintRules) {
    this.rules = [...rules]
  }

  /** Add a new hint rule */
  addRule(rule: HintRule): void {
    this.rules.push(rule)
  }

  /** Process output and return any triggered hints */
  processOutput(output: string): Hint[] {
    const hints: Hint[] = []
    const now = Date.now()

    for (const rule of this.rules) {
      // Check if pattern matches
      const isMatch =
        typeof rule.pattern === 'string'
          ? output.includes(rule.pattern)
          : rule.pattern.test(output)

      if (!isMatch) continue

      // Check once restriction
      const ruleId = this.getRuleId(rule)
      if (rule.once && this.triggeredOnce.has(ruleId)) continue

      // Check cooldown
      const lastTime = this.lastHintTime.get(ruleId) || 0
      if (rule.cooldown && now - lastTime < rule.cooldown) continue

      // Create hint
      const hint: Hint = {
        id: `hint-${++this.hintIdCounter}`,
        ...rule.hint,
      }

      hints.push(hint)
      this.activeHints.set(hint.id, hint)

      // Track restrictions
      if (rule.once) this.triggeredOnce.add(ruleId)
      this.lastHintTime.set(ruleId, now)

      // Emit event
      docsEventBus.emit('hint:show', {
        message: hint.message,
        type: hint.type,
      })

      // Auto-hide after timeout
      if (hint.timeout) {
        setTimeout(() => {
          this.dismissHint(hint.id)
        }, hint.timeout)
      }
    }

    return hints
  }

  /** Process pattern matches from PatternMatcher */
  processMatches(matches: PatternMatch[]): Hint[] {
    const hints: Hint[] = []

    for (const match of matches) {
      if (match.type === 'error' && match.message) {
        const hint: Hint = {
          id: `hint-${++this.hintIdCounter}`,
          message: match.message,
          type: 'error',
          suggestion: match.suggestion,
        }
        hints.push(hint)
        this.activeHints.set(hint.id, hint)

        docsEventBus.emit('hint:show', {
          message: hint.message,
          type: hint.type,
        })
      }
    }

    return hints
  }

  /** Dismiss a hint */
  dismissHint(hintId: string): void {
    if (this.activeHints.has(hintId)) {
      this.activeHints.delete(hintId)
      docsEventBus.emit('hint:hide', undefined)
    }
  }

  /** Get all active hints */
  getActiveHints(): Hint[] {
    return Array.from(this.activeHints.values())
  }

  /** Clear all hints */
  clearAll(): void {
    this.activeHints.clear()
    docsEventBus.emit('hint:hide', undefined)
  }

  /** Reset the service (clear triggers and cooldowns) */
  reset(): void {
    this.triggeredOnce.clear()
    this.lastHintTime.clear()
    this.activeHints.clear()
  }

  private getRuleId(rule: HintRule): string {
    const pattern =
      typeof rule.pattern === 'string' ? rule.pattern : rule.pattern.source
    return `${pattern}:${rule.hint.message}`
  }
}

// Export singleton
export const hintsService = new HintsService()
