import { LitElement, html, css, nothing } from 'lit'
import { property, state, query } from 'lit/decorators.js'

export const TAG_NAME = 'skillet-xlsx-tutorial'

interface Section {
  id: string
  title: string
  terminal: string[] // Lines to show in terminal for this section
}

/**
 * Excel formulas use case tutorial with Stripe-style layout.
 * Sections scroll on left, terminal updates on right based on visible section.
 */
export class SkilletXlsxTutorial extends LitElement {
  static styles = css`
    :host {
      display: block;
      --nav-height: 0px;
    }

    .layout {
      display: flex;
      min-height: 100vh;
    }

    /* Left column - scrollable content */
    .content {
      width: 50%;
      padding: 48px;
      overflow-y: auto;
    }

    /* Right column - sticky terminal */
    .terminal-column {
      width: 50%;
      background: #111;
    }

    .terminal-sticky {
      position: sticky;
      top: 0;
      height: 100vh;
      padding: 24px;
      display: flex;
      flex-direction: column;
      box-sizing: border-box;
    }

    .terminal-wrapper {
      flex: 1;
      background: #0a0a0a;
      border-radius: 12px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      border: 1px solid #333;
    }

    .terminal-header {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 12px 16px;
      background: #1a1a1a;
      border-bottom: 1px solid #333;
    }

    .terminal-dot {
      width: 12px;
      height: 12px;
      border-radius: 50%;
    }
    .terminal-dot.red { background: #ff5f56; }
    .terminal-dot.yellow { background: #ffbd2e; }
    .terminal-dot.green { background: #27c93f; }

    .terminal-title {
      flex: 1;
      text-align: center;
      font-size: 13px;
      color: #666;
      font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .terminal-body {
      flex: 1;
      overflow: auto;
      padding: 20px;
      font-family: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
      font-size: 13px;
      line-height: 1.7;
      color: #e0e0e0;
    }

    .terminal-line {
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
    }

    .terminal-line.prompt {
      color: #4ade80;
    }

    .terminal-line.command {
      color: #60a5fa;
    }

    .terminal-line.comment {
      color: #6b7280;
    }

    .terminal-line.error {
      color: #f87171;
    }

    .terminal-line.success {
      color: #4ade80;
    }

    .terminal-line.highlight {
      background: rgba(251, 191, 36, 0.1);
      margin: 0 -20px;
      padding: 0 20px;
      border-left: 3px solid #fbbf24;
    }

    .section-indicator {
      padding: 12px 16px;
      background: #1a1a1a;
      border-top: 1px solid #333;
      font-size: 12px;
      color: #888;
      font-family: -apple-system, BlinkMacSystemFont, sans-serif;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .section-indicator .step {
      color: #4ade80;
      font-weight: 600;
    }

    .section-indicator .dots {
      display: flex;
      gap: 6px;
      margin-left: auto;
    }

    .section-indicator .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #333;
    }

    .section-indicator .dot.active {
      background: #4ade80;
    }

    .section-indicator .dot.completed {
      background: #22c55e;
    }

    /* Content styles */
    .section {
      min-height: 60vh;
      padding-bottom: 48px;
      border-bottom: 1px solid #e5e5e5;
    }

    .section:last-child {
      border-bottom: none;
      min-height: auto;
      padding-bottom: 120px;
    }

    h1 {
      font-size: 2.25rem;
      font-weight: 700;
      margin: 0 0 8px 0;
      line-height: 1.2;
      color: #111;
    }

    .subtitle {
      font-size: 1.125rem;
      color: #6b7280;
      margin: 0 0 32px 0;
    }

    h2 {
      font-size: 1.5rem;
      font-weight: 600;
      margin: 0 0 16px 0;
      color: #111;
    }

    p {
      margin: 0 0 16px 0;
      line-height: 1.7;
      color: #374151;
      font-size: 1rem;
    }

    ul {
      margin: 0 0 16px 0;
      padding-left: 24px;
      color: #374151;
    }

    li {
      margin-bottom: 8px;
      line-height: 1.6;
    }

    code {
      background: #f3f4f6;
      padding: 2px 6px;
      border-radius: 4px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.875em;
      color: #dc2626;
    }

    pre {
      background: #1e1e1e;
      padding: 16px;
      border-radius: 8px;
      overflow-x: auto;
      margin: 16px 0;
    }

    pre code {
      background: none;
      padding: 0;
      color: #e0e0e0;
      font-size: 13px;
      line-height: 1.6;
    }

    .step-badge {
      display: inline-block;
      background: #dbeafe;
      color: #1d4ed8;
      font-size: 0.75rem;
      font-weight: 600;
      padding: 4px 10px;
      border-radius: 12px;
      margin-bottom: 12px;
    }

    .result-box {
      background: #f0fdf4;
      border: 1px solid #86efac;
      border-radius: 8px;
      padding: 16px;
      margin: 16px 0;
    }

    .result-box.fail {
      background: #fef2f2;
      border-color: #fca5a5;
    }

    .result-box .score {
      font-size: 1.5rem;
      font-weight: 700;
      color: #16a34a;
    }

    .result-box.fail .score {
      color: #dc2626;
    }

    /* Responsive */
    @media (max-width: 1000px) {
      .layout {
        flex-direction: column;
      }
      .content,
      .terminal-column {
        width: 100%;
      }
      .terminal-sticky {
        position: relative;
        height: 50vh;
      }
      .section {
        min-height: auto;
      }
    }
  `

  @state() private currentSectionIndex = 0

  private sections: Section[] = [
    {
      id: 'intro',
      title: 'The Problem',
      terminal: [
        '$ claude',
        '',
        '> Create an Excel file that calculates monthly revenue.',
        '  January: 100 units at $50 each.',
        '  February: 120 units at $52 each.',
        '  Include a total row.',
        '',
        '● Creating spreadsheet...',
        '',
        '# Claude writes:',
        'from openpyxl import Workbook',
        '',
        'wb = Workbook()',
        'sheet = wb.active',
        '',
        "sheet['A1'] = 'Month'",
        "sheet['B1'] = 'Units'",
        "sheet['C1'] = 'Price'",
        "sheet['D1'] = 'Revenue'",
        '',
        "sheet['A2'] = 'January'",
        "sheet['B2'] = 100",
        "sheet['C2'] = 50",
        "sheet['D2'] = 5000      # ⚠️ Hardcoded!",
        '',
        "sheet['A3'] = 'February'",
        "sheet['B3'] = 120",
        "sheet['C3'] = 52",
        "sheet['D3'] = 6240      # ⚠️ Hardcoded!",
        '',
        "sheet['A4'] = 'Total'",
        "sheet['D4'] = 11240     # ⚠️ Not a formula!",
        '',
        "wb.save('revenue.xlsx')",
        '',
        '✓ Created revenue.xlsx',
      ],
    },
    {
      id: 'step1',
      title: 'Step 1: Identify Gaps',
      terminal: [
        '# What Claude wrote (WRONG):',
        '',
        "sheet['D2'] = 5000      # Hardcoded value",
        "sheet['D3'] = 6240      # Hardcoded value",
        "sheet['D4'] = 11240     # Hardcoded value",
        '',
        '# What it SHOULD be:',
        '',
        "sheet['D2'] = '=B2*C2'       # Formula!",
        "sheet['D3'] = '=B3*C3'       # Formula!",
        "sheet['D4'] = '=SUM(D2:D3)'  # Formula!",
        '',
        '─────────────────────────────────────',
        '',
        'The spreadsheet LOOKS correct but:',
        '',
        '• Change units from 100 → 150',
        '  Revenue still shows $5,000 ❌',
        '',
        '• The "total" is just a number',
        '  Not actually summing anything ❌',
        '',
        "• It's a picture of a spreadsheet",
        '  Not a real spreadsheet ❌',
      ],
    },
    {
      id: 'step2',
      title: 'Step 2: Create Evaluations',
      terminal: [
        '$ /skillet:add',
        '',
        '┌─────────────────────────────────────┐',
        '│ Capture a new evaluation            │',
        '└─────────────────────────────────────┘',
        '',
        'What prompt triggered this behavior?',
        '> Create an Excel file that calculates',
        '  monthly revenue with units and prices',
        '',
        'What went wrong?',
        '> Used hardcoded values (5000) instead',
        '  of formulas (=B2*C2)',
        '',
        'What should have happened?',
        '> Revenue cells should use formulas.',
        '  Total should use =SUM()',
        '',
        '✓ Created evals/xlsx-formulas/',
        '    001-uses-formulas.yaml',
        '',
        '─────────────────────────────────────',
        '',
        '$ cat evals/xlsx-formulas/001-uses-formulas.yaml',
        '',
        'prompt: |',
        '  Create an Excel file with Q1 sales...',
        'expected: |',
        '  Uses Excel formulas for calculations.',
        '  Revenue cells contain =A2*B2 style.',
        '  Total cell contains =SUM() formula.',
      ],
    },
    {
      id: 'step3',
      title: 'Step 3: Establish Baseline',
      terminal: [
        '$ skillet eval xlsx-formulas',
        '',
        'Running 4 evaluations...',
        '',
        '┌────────────────────────────────────────┐',
        '│ xlsx-formulas                          │',
        '├────────────────────────────────────────┤',
        '│                                        │',
        '│  001-uses-formulas      ❌ FAIL        │',
        '│    Expected: formulas like =A2*B2      │',
        '│    Got: hardcoded value 5000           │',
        '│                                        │',
        '│  002-recalculates       ✓ PASS         │',
        '│                                        │',
        '│  003-no-errors          ❌ FAIL        │',
        '│    Found: #REF! error in cell E2       │',
        '│                                        │',
        '│  004-formatting         ❌ FAIL        │',
        '│    Expected: blue input cells          │',
        '│    Got: no color coding                │',
        '│                                        │',
        '├────────────────────────────────────────┤',
        '│  Results: 1/4 passing (25%)            │',
        '└────────────────────────────────────────┘',
        '',
        'This is your BASELINE.',
        'Without a skill, Claude scores 25%.',
      ],
    },
    {
      id: 'step4',
      title: 'Step 4: Write Skill',
      terminal: [
        '$ cat skills/xlsx-formulas/SKILL.md',
        '',
        '---',
        'name: xlsx-formulas',
        'description: Create Excel spreadsheets',
        '  with proper formulas.',
        '---',
        '',
        '# Excel with Formulas',
        '',
        '**Always use formulas for calculations.**',
        '',
        '## Critical Rule',
        '',
        '❌ WRONG:',
        "  sheet['B10'] = 5000",
        '',
        '✅ CORRECT:',
        "  sheet['B10'] = '=SUM(B2:B9)'",
        '',
        '## Common Formulas',
        '',
        "  '=A2*B2'        # Multiply",
        "  '=SUM(C2:C9)'   # Sum range",
        "  '=(B2-B1)/B1'   # Growth rate",
        '',
        '## Formatting',
        '',
        '• Blue text: Input values',
        '• Black text: Formulas',
        '• Run recalc.py after saving',
      ],
    },
    {
      id: 'step5',
      title: 'Step 5: Iterate',
      terminal: [
        '$ skillet eval xlsx-formulas',
        '',
        'Running 4 evaluations with skill...',
        '',
        '┌────────────────────────────────────────┐',
        '│ xlsx-formulas (with skill)             │',
        '├────────────────────────────────────────┤',
        '│                                        │',
        '│  001-uses-formulas      ✓ PASS ✨      │',
        '│    Now using: =B2*C2                   │',
        '│                                        │',
        '│  002-recalculates       ✓ PASS         │',
        '│                                        │',
        '│  003-no-errors          ✓ PASS ✨      │',
        '│    No formula errors found             │',
        '│                                        │',
        '│  004-formatting         ✓ PASS ✨      │',
        '│    Input cells now blue                │',
        '│                                        │',
        '├────────────────────────────────────────┤',
        '│  Results: 4/4 passing (100%) 🎉        │',
        '└────────────────────────────────────────┘',
        '',
        '25% → 100%',
        '',
        'The skill WORKS.',
        'The evals PROVE it.',
      ],
    },
  ]

  connectedCallback() {
    super.connectedCallback()
    this.setupIntersectionObserver()
  }

  private setupIntersectionObserver() {
    // Wait for render
    this.updateComplete.then(() => {
      const sections = this.shadowRoot?.querySelectorAll('.section')
      if (!sections) return

      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              const index = parseInt(entry.target.getAttribute('data-index') || '0')
              this.currentSectionIndex = index
            }
          })
        },
        { threshold: 0.3, rootMargin: '-20% 0px -60% 0px' }
      )

      sections.forEach((section) => observer.observe(section))
    })
  }

  private renderTerminalLine(line: string) {
    let className = 'terminal-line'

    if (line.startsWith('$') || line.startsWith('>')) {
      className += ' prompt'
    } else if (line.startsWith('#')) {
      className += ' comment'
    } else if (line.includes('❌') || line.includes('FAIL') || line.includes('⚠️')) {
      className += ' error'
    } else if (line.includes('✓') || line.includes('✨') || line.includes('🎉')) {
      className += ' success'
    } else if (line.includes('Hardcoded') || line.includes('WRONG')) {
      className += ' highlight'
    }

    return html`<div class="${className}">${line}</div>`
  }

  render() {
    const currentSection = this.sections[this.currentSectionIndex]

    return html`
      <div class="layout">
        <div class="content">
          <!-- Intro Section -->
          <div class="section" data-index="0">
            <h1>Excel Formulas</h1>
            <p class="subtitle">Teaching Claude to create dynamic spreadsheets instead of static tables.</p>

            <h2>The Problem</h2>
            <p>Claude can generate Excel files using openpyxl. But without guidance, it takes shortcuts:</p>
            <ul>
              <li><strong>Hardcodes values</strong> instead of using formulas</li>
              <li>Creates spreadsheets that <strong>don't update</strong> when inputs change</li>
              <li>Misses financial modeling conventions (color coding, formatting)</li>
              <li>Produces formula errors (<code>#REF!</code>, <code>#DIV/0!</code>)</li>
            </ul>
            <p>Watch the terminal → Claude writes <code>sheet['D2'] = 5000</code> instead of <code>sheet['D2'] = '=B2*C2'</code>. The spreadsheet <em>looks</em> right but doesn't work like one.</p>
          </div>

          <!-- Step 1 -->
          <div class="section" data-index="1">
            <span class="step-badge">Step 1 of 5</span>
            <h2>Identify Gaps</h2>
            <p>First, we ask Claude to create a spreadsheet and observe what goes wrong:</p>
            <pre><code>"Create an Excel file that calculates monthly revenue.
January: 100 units at $50 each.
February: 120 units at $52 each.
Include a total row."</code></pre>
            <p>The terminal shows Claude's response. Notice the hardcoded values where formulas should be.</p>
            <p>This is the <strong>gap</strong> we want to fix. Claude doesn't know our preference for formulas over calculated values.</p>
          </div>

          <!-- Step 2 -->
          <div class="section" data-index="2">
            <span class="step-badge">Step 2 of 5</span>
            <h2>Create Evaluations</h2>
            <p>Now we <strong>capture</strong> this failure as an evaluation. This is the core Skillet workflow:</p>
            <pre><code>/skillet:add</code></pre>
            <p>Skillet asks three questions:</p>
            <ul>
              <li><strong>What prompt</strong> triggered this behavior?</li>
              <li><strong>What went wrong</strong> with the response?</li>
              <li><strong>What should have happened</strong> instead?</li>
            </ul>
            <p>The result is a YAML file that codifies our expectations. We create several of these to cover different failure modes.</p>
          </div>

          <!-- Step 3 -->
          <div class="section" data-index="3">
            <span class="step-badge">Step 3 of 5</span>
            <h2>Establish Baseline</h2>
            <p>Run the evaluations <em>without</em> a skill to see how Claude performs by default:</p>
            <pre><code>skillet eval xlsx-formulas</code></pre>
            <div class="result-box fail">
              <div class="score">25% (1/4)</div>
              <p style="margin:8px 0 0 0;color:#991b1b;">This is our baseline. Claude knows formulas exist but doesn't use them consistently.</p>
            </div>
            <p>Now we know exactly where the gaps are—and we have a number to improve.</p>
          </div>

          <!-- Step 4 -->
          <div class="section" data-index="4">
            <span class="step-badge">Step 4 of 5</span>
            <h2>Write Minimal Instructions</h2>
            <p>Create a skill file with <strong>just enough</strong> guidance to fix the failures:</p>
            <pre><code>skills/xlsx-formulas/SKILL.md</code></pre>
            <p>The skill is minimal—we're not writing a textbook. Just the critical rules:</p>
            <ul>
              <li>Always use formulas for calculated values</li>
              <li>Common formula patterns</li>
              <li>Formatting conventions</li>
            </ul>
            <p>Less is more. We'll iterate if needed.</p>
          </div>

          <!-- Step 5 -->
          <div class="section" data-index="5">
            <span class="step-badge">Step 5 of 5</span>
            <h2>Iterate</h2>
            <p>Run the evaluations again—now <em>with</em> the skill:</p>
            <pre><code>skillet eval xlsx-formulas</code></pre>
            <div class="result-box">
              <div class="score">100% (4/4) 🎉</div>
              <p style="margin:8px 0 0 0;color:#166534;">The skill works. Claude now uses formulas consistently.</p>
            </div>
            <p>The journey: <strong>25% → 100%</strong></p>
            <p>The evals are your proof. Re-run them anytime to verify the skill still works. When you update the skill later, you'll know immediately if you broke something.</p>
          </div>
        </div>

        <div class="terminal-column">
          <div class="terminal-sticky">
            <div class="terminal-wrapper">
              <div class="terminal-header">
                <span class="terminal-dot red"></span>
                <span class="terminal-dot yellow"></span>
                <span class="terminal-dot green"></span>
                <span class="terminal-title">Claude Code</span>
              </div>
              <div class="terminal-body">
                ${currentSection.terminal.map((line) => this.renderTerminalLine(line))}
              </div>
              <div class="section-indicator">
                <span class="step">${currentSection.title}</span>
                <div class="dots">
                  ${this.sections.map(
                    (_, i) => html`
                      <span class="dot ${i < this.currentSectionIndex ? 'completed' : ''} ${i === this.currentSectionIndex ? 'active' : ''}"></span>
                    `
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    `
  }
}
