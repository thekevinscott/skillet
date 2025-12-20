/**
 * Pattern matching service for reactive docs.
 * Watches terminal output and detects patterns that trigger reactive behaviors.
 */

export interface PatternMatch {
  type: 'step-complete' | 'error' | 'hint' | 'custom'
  pattern: string | RegExp
  message?: string
  suggestion?: string
  data?: Record<string, unknown>
}

export interface PatternRule {
  /** Pattern to match (string for exact, regex for fuzzy) */
  pattern: string | RegExp
  /** Type of match */
  type: PatternMatch['type']
  /** Message to show when matched */
  message?: string
  /** Suggested action or fix */
  suggestion?: string
  /** Whether to stop checking after this match */
  stopOnMatch?: boolean
  /** Minimum buffer size before checking */
  minBufferSize?: number
}

// Common error patterns for helpful suggestions
export const commonErrorPatterns: PatternRule[] = [
  // npm errors
  {
    pattern: /npm ERR! code ENOENT/,
    type: 'error',
    message: 'File or directory not found',
    suggestion: 'Check that the file path is correct',
  },
  {
    pattern: /npm ERR! code E404/,
    type: 'error',
    message: 'Package not found',
    suggestion: 'Verify the package name is spelled correctly',
  },
  {
    pattern: /Cannot find module '([^']+)'/,
    type: 'error',
    message: 'Missing module',
    suggestion: 'Try running: npm install',
  },

  // Git errors
  {
    pattern: /fatal: not a git repository/,
    type: 'error',
    message: 'Not in a git repository',
    suggestion: 'Run: git init',
  },
  {
    pattern: /error: failed to push/,
    type: 'error',
    message: 'Push failed',
    suggestion: 'Try pulling first: git pull --rebase',
  },

  // Permission errors
  {
    pattern: /Permission denied/i,
    type: 'error',
    message: 'Permission denied',
    suggestion: 'You may need elevated permissions',
  },

  // Command not found
  {
    pattern: /command not found|not recognized/i,
    type: 'error',
    message: 'Command not found',
    suggestion: 'Check that the command is installed and in your PATH',
  },

  // Python errors
  {
    pattern: /ModuleNotFoundError: No module named '([^']+)'/,
    type: 'error',
    message: 'Python module not found',
    suggestion: 'Try: pip install $1',
  },

  // TypeScript errors
  {
    pattern: /error TS\d+:/,
    type: 'error',
    message: 'TypeScript compilation error',
  },
]

export class PatternMatcher {
  private rules: PatternRule[] = []
  private buffer = ''
  private maxBufferSize = 10000

  constructor(rules: PatternRule[] = []) {
    this.rules = [...commonErrorPatterns, ...rules]
  }

  /** Add a new pattern rule */
  addRule(rule: PatternRule): void {
    this.rules.push(rule)
  }

  /** Add multiple rules */
  addRules(rules: PatternRule[]): void {
    this.rules.push(...rules)
  }

  /** Remove rules by type */
  removeRulesByType(type: PatternMatch['type']): void {
    this.rules = this.rules.filter((r) => r.type !== type)
  }

  /** Clear all custom rules (keeps common error patterns) */
  clearCustomRules(): void {
    this.rules = [...commonErrorPatterns]
  }

  /** Append output to buffer and check for matches */
  processOutput(output: string): PatternMatch[] {
    this.buffer += output

    // Trim buffer if too large (keep recent content)
    if (this.buffer.length > this.maxBufferSize) {
      this.buffer = this.buffer.slice(-this.maxBufferSize / 2)
    }

    return this.checkPatterns()
  }

  /** Check buffer against all patterns */
  private checkPatterns(): PatternMatch[] {
    const matches: PatternMatch[] = []

    for (const rule of this.rules) {
      // Skip if buffer too small
      if (rule.minBufferSize && this.buffer.length < rule.minBufferSize) {
        continue
      }

      const isMatch =
        typeof rule.pattern === 'string'
          ? this.buffer.includes(rule.pattern)
          : rule.pattern.test(this.buffer)

      if (isMatch) {
        const match: PatternMatch = {
          type: rule.type,
          pattern:
            typeof rule.pattern === 'string'
              ? rule.pattern
              : rule.pattern.source,
          message: rule.message,
          suggestion: rule.suggestion,
        }

        // Extract capture groups if regex
        if (typeof rule.pattern !== 'string') {
          const regexMatch = this.buffer.match(rule.pattern)
          if (regexMatch && regexMatch.length > 1) {
            // Replace $1, $2, etc. in message/suggestion
            match.message = match.message?.replace(/\$(\d+)/g, (_, i) => regexMatch[+i] || '')
            match.suggestion = match.suggestion?.replace(/\$(\d+)/g, (_, i) => regexMatch[+i] || '')
            match.data = { captures: regexMatch.slice(1) }
          }
        }

        matches.push(match)

        if (rule.stopOnMatch) {
          break
        }
      }
    }

    return matches
  }

  /** Clear the buffer */
  clearBuffer(): void {
    this.buffer = ''
  }

  /** Get current buffer content */
  getBuffer(): string {
    return this.buffer
  }

  /** Check a single pattern against current buffer */
  checkPattern(pattern: string | RegExp): boolean {
    return typeof pattern === 'string'
      ? this.buffer.includes(pattern)
      : pattern.test(this.buffer)
  }
}

// Export singleton for shared use
export const patternMatcher = new PatternMatcher()
