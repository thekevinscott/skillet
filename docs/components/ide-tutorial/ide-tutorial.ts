import { LitElement, html, css, nothing } from 'lit'
import { property, state, query } from 'lit/decorators.js'
import { Terminal as XTerm } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import { WebContainer } from '@webcontainer/api'

export const TAG_NAME = 'skillet-ide-tutorial'

interface FileNode {
  name: string
  type: 'file' | 'folder'
  content?: string
  children?: FileNode[]
  icon?: string
}

interface Tab {
  id: string
  name: string
  type: 'file' | 'guide' | 'terminal'
  content?: string
}

/**
 * IDE-style tutorial that looks like VS Code.
 * File tree on left, tabbed editor in center, terminal at bottom.
 */
export class SkilletIdeTutorial extends LitElement {
  static styles = css`
    :host {
      display: block;
      height: 100%;
      min-height: 600px;
    }

    .ide {
      height: 100%;
      display: flex;
      flex-direction: column;
      background: #1e1e1e;
      border-radius: 8px;
      overflow: hidden;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }

    /* Title bar */
    .title-bar {
      display: flex;
      align-items: center;
      padding: 8px 12px;
      background: #323233;
      border-bottom: 1px solid #000;
    }

    .traffic-lights {
      display: flex;
      gap: 8px;
    }

    .dot {
      width: 12px;
      height: 12px;
      border-radius: 50%;
    }
    .dot.red { background: #ff5f56; }
    .dot.yellow { background: #ffbd2e; }
    .dot.green { background: #27c93f; }

    .title-text {
      flex: 1;
      text-align: center;
      font-size: 13px;
      color: #999;
    }

    /* Main content */
    .main {
      flex: 1;
      display: flex;
      min-height: 0;
    }

    /* Sidebar */
    .sidebar {
      width: 240px;
      background: #252526;
      border-right: 1px solid #000;
      display: flex;
      flex-direction: column;
    }

    .sidebar-header {
      padding: 12px;
      font-size: 11px;
      font-weight: 600;
      color: #ccc;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .file-tree {
      flex: 1;
      overflow-y: auto;
      padding: 0 8px;
    }

    .file-item {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 4px 8px;
      border-radius: 4px;
      cursor: pointer;
      font-size: 13px;
      color: #ccc;
    }

    .file-item:hover {
      background: #2a2d2e;
    }

    .file-item.active {
      background: #37373d;
    }

    .file-item.guide {
      color: #4ec9b0;
    }

    .file-icon {
      width: 16px;
      text-align: center;
      font-size: 12px;
    }

    /* Editor area */
    .editor-area {
      flex: 1;
      display: flex;
      flex-direction: column;
      min-width: 0;
    }

    /* Tabs */
    .tabs {
      display: flex;
      background: #252526;
      border-bottom: 1px solid #000;
    }

    .tab {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 16px;
      background: #2d2d2d;
      border-right: 1px solid #000;
      font-size: 13px;
      color: #999;
      cursor: pointer;
    }

    .tab:hover {
      background: #2a2d2e;
    }

    .tab.active {
      background: #1e1e1e;
      color: #fff;
      border-bottom: 1px solid #1e1e1e;
      margin-bottom: -1px;
    }

    .tab-close {
      width: 16px;
      height: 16px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 4px;
      font-size: 14px;
      opacity: 0.5;
    }

    .tab-close:hover {
      background: #313131;
      opacity: 1;
    }

    /* Editor content */
    .editor-content {
      flex: 1;
      overflow: auto;
      min-height: 0;
    }

    .guide-content {
      padding: 32px;
      color: #d4d4d4;
      line-height: 1.7;
    }

    .guide-content h1 {
      font-size: 28px;
      font-weight: 600;
      color: #fff;
      margin: 0 0 16px 0;
      padding-bottom: 16px;
      border-bottom: 1px solid #333;
    }

    .guide-content h2 {
      font-size: 20px;
      font-weight: 600;
      color: #4ec9b0;
      margin: 32px 0 16px 0;
    }

    .guide-content p {
      margin: 0 0 16px 0;
    }

    .guide-content code {
      background: #2d2d2d;
      padding: 2px 6px;
      border-radius: 4px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 13px;
      color: #ce9178;
    }

    .guide-content pre {
      background: #2d2d2d;
      padding: 16px;
      border-radius: 4px;
      overflow-x: auto;
      margin: 16px 0;
    }

    .guide-content pre code {
      background: none;
      padding: 0;
      color: #d4d4d4;
    }

    .guide-content .action-btn {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 10px 20px;
      background: #0e639c;
      color: #fff;
      border: none;
      border-radius: 4px;
      font-size: 14px;
      cursor: pointer;
      margin-top: 8px;
    }

    .guide-content .action-btn:hover {
      background: #1177bb;
    }

    /* Code view */
    .code-view {
      height: 100%;
      padding: 16px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 14px;
      line-height: 1.5;
      color: #d4d4d4;
      white-space: pre;
    }

    .code-view .line-number {
      display: inline-block;
      width: 40px;
      color: #6e7681;
      user-select: none;
    }

    /* Terminal panel */
    .terminal-panel {
      height: 200px;
      border-top: 1px solid #000;
      display: flex;
      flex-direction: column;
    }

    .terminal-header {
      display: flex;
      align-items: center;
      padding: 8px 12px;
      background: #252526;
      border-bottom: 1px solid #333;
    }

    .terminal-header span {
      font-size: 12px;
      color: #ccc;
      font-weight: 500;
    }

    .terminal-container {
      flex: 1;
      min-height: 0;
    }

    /* Activity bar */
    .activity-bar {
      width: 48px;
      background: #333;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 8px 0;
      gap: 4px;
    }

    .activity-icon {
      width: 40px;
      height: 40px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 8px;
      font-size: 20px;
      color: #858585;
      cursor: pointer;
    }

    .activity-icon:hover {
      color: #fff;
    }

    .activity-icon.active {
      color: #fff;
      background: #37373d;
    }
  `

  @state() private tabs: Tab[] = [
    { id: 'welcome', name: 'WELCOME.md', type: 'guide' },
  ]
  @state() private activeTab = 'welcome'
  @state() private terminalReady = false

  @query('.terminal-container') private terminalContainer!: HTMLDivElement

  private xterm: XTerm | null = null
  private fitAddon: FitAddon | null = null
  private container: WebContainer | null = null
  private inputWriter: WritableStreamDefaultWriter | null = null

  private files: FileNode[] = [
    { name: 'WELCOME.md', type: 'file', icon: '📖' },
    { name: 'STEP-1.md', type: 'file', icon: '1️⃣' },
    { name: 'STEP-2.md', type: 'file', icon: '2️⃣' },
    { name: 'STEP-3.md', type: 'file', icon: '3️⃣' },
    {
      name: 'src',
      type: 'folder',
      children: [
        { name: 'greeting.js', type: 'file', icon: '📄', content: 'console.log("Welcome to Skillet!");' },
        { name: 'hello.txt', type: 'file', icon: '📄', content: 'Hello, World!' },
      ],
    },
  ]

  private guides: Record<string, string> = {
    'WELCOME.md': `
# Welcome to Skillet

This interactive tutorial will teach you the basics of Skillet - an evaluation-driven framework for teaching Claude Code new skills.

## What You'll Learn

1. How to navigate the terminal environment
2. Running commands and scripts
3. Creating and editing files
4. Understanding the evaluation workflow

## Getting Started

Open **STEP-1.md** from the file explorer on the left to begin.

Or, try running a command in the terminal below:

\`\`\`bash
echo "Hello from the terminal!"
\`\`\`

<button class="action-btn" onclick="this.getRootNode().host.runCommand('echo \\"Hello from the terminal!\\"')">
▶ Run in Terminal
</button>
    `,
    'STEP-1.md': `
# Step 1: Exploring Files

Let's explore what's in your workspace.

## List Files

Run \`ls -la\` in the terminal to see all files:

\`\`\`bash
ls -la
\`\`\`

<button class="action-btn" onclick="this.getRootNode().host.runCommand('ls -la')">
▶ Run in Terminal
</button>

## Read a File

You can read file contents with \`cat\`:

\`\`\`bash
cat src/hello.txt
\`\`\`

<button class="action-btn" onclick="this.getRootNode().host.runCommand('cat src/hello.txt')">
▶ Run in Terminal
</button>

When you're ready, open **STEP-2.md** to continue.
    `,
    'STEP-2.md': `
# Step 2: Running JavaScript

Node.js is available in your environment. Let's run some code!

## Run a Script

There's a greeting script in the src folder. Run it with:

\`\`\`bash
node src/greeting.js
\`\`\`

<button class="action-btn" onclick="this.getRootNode().host.runCommand('node src/greeting.js')">
▶ Run in Terminal
</button>

## Run Inline Code

You can also run JavaScript directly:

\`\`\`bash
node -e "console.log('2 + 2 =', 2 + 2)"
\`\`\`

<button class="action-btn" onclick="this.getRootNode().host.runCommand('node -e \\"console.log(2 + 2)\\"')">
▶ Run in Terminal
</button>

Open **STEP-3.md** to continue.
    `,
    'STEP-3.md': `
# Step 3: Creating Files

Let's create something new!

## Write a File

Use echo with redirection to create a file:

\`\`\`bash
echo "I made this with Skillet!" > myfile.txt
\`\`\`

<button class="action-btn" onclick="this.getRootNode().host.runCommand('echo \\"I made this!\\" > myfile.txt')">
▶ Run in Terminal
</button>

## Verify It

Read your new file:

\`\`\`bash
cat myfile.txt
\`\`\`

<button class="action-btn" onclick="this.getRootNode().host.runCommand('cat myfile.txt')">
▶ Run in Terminal
</button>

## 🎉 Congratulations!

You've completed the basics. You now know how to:
- Navigate files
- Run JavaScript
- Create new files

Ready to build something? Check out the [Getting Started](/getting-started) guide.
    `,
  }

  async firstUpdated() {
    await this.initTerminal()
  }

  private async initTerminal() {
    this.xterm = new XTerm({
      cursorBlink: true,
      fontSize: 13,
      fontFamily: '"JetBrains Mono", Menlo, Monaco, monospace',
      theme: {
        background: '#1e1e1e',
        foreground: '#d4d4d4',
      },
    })

    this.fitAddon = new FitAddon()
    this.xterm.loadAddon(this.fitAddon)
    this.xterm.open(this.terminalContainer)
    this.fitAddon.fit()

    this.xterm.writeln('\x1b[90mBooting WebContainer...\x1b[0m')

    try {
      this.container = await WebContainer.boot()
      await this.container.mount({
        src: {
          directory: {
            'greeting.js': { file: { contents: 'console.log("Welcome to Skillet!");' } },
            'hello.txt': { file: { contents: 'Hello, World!' } },
          },
        },
      })

      const shellProcess = await this.container.spawn('jsh', {
        terminal: { cols: this.xterm.cols, rows: this.xterm.rows },
      })

      shellProcess.output.pipeTo(
        new WritableStream({
          write: (data) => this.xterm?.write(data),
        })
      )

      this.inputWriter = shellProcess.input.getWriter()
      this.xterm.onData((data) => this.inputWriter?.write(data))

      new ResizeObserver(() => {
        this.fitAddon?.fit()
        shellProcess.resize({ cols: this.xterm!.cols, rows: this.xterm!.rows })
      }).observe(this.terminalContainer)

      this.terminalReady = true
      this.xterm.write('\r\x1b[K\x1b[32m✓ Ready\x1b[0m\n\n')
    } catch (err) {
      this.xterm.writeln(`\x1b[31mError: ${err}\x1b[0m`)
    }
  }

  async runCommand(command: string) {
    if (!this.inputWriter) return
    for (const char of command) {
      await this.inputWriter.write(char)
      await new Promise((r) => setTimeout(r, 20))
    }
    await this.inputWriter.write('\n')
  }

  private openFile(fileName: string) {
    if (!this.tabs.find((t) => t.name === fileName)) {
      this.tabs = [...this.tabs, { id: fileName, name: fileName, type: 'guide' }]
    }
    this.activeTab = fileName
  }

  private closeTab(id: string) {
    this.tabs = this.tabs.filter((t) => t.id !== id)
    if (this.activeTab === id && this.tabs.length > 0) {
      this.activeTab = this.tabs[0].id
    }
  }

  private renderFileTree(nodes: FileNode[], depth = 0): unknown {
    return nodes.map((node) => html`
      ${node.type === 'folder'
        ? html`
            <div class="file-item" style="padding-left: ${depth * 12 + 8}px">
              <span class="file-icon">📁</span>
              <span>${node.name}</span>
            </div>
            ${node.children ? this.renderFileTree(node.children, depth + 1) : nothing}
          `
        : html`
            <div
              class="file-item ${this.activeTab === node.name ? 'active' : ''} ${node.name.endsWith('.md') ? 'guide' : ''}"
              style="padding-left: ${depth * 12 + 8}px"
              @click=${() => this.openFile(node.name)}
            >
              <span class="file-icon">${node.icon || '📄'}</span>
              <span>${node.name}</span>
            </div>
          `}
    `)
  }

  render() {
    const activeGuide = this.guides[this.activeTab] || ''

    return html`
      <div class="ide">
        <div class="title-bar">
          <div class="traffic-lights">
            <span class="dot red"></span>
            <span class="dot yellow"></span>
            <span class="dot green"></span>
          </div>
          <span class="title-text">Skillet Tutorial — Interactive IDE</span>
        </div>

        <div class="main">
          <div class="activity-bar">
            <div class="activity-icon active">📁</div>
            <div class="activity-icon">🔍</div>
            <div class="activity-icon">⚙️</div>
          </div>

          <div class="sidebar">
            <div class="sidebar-header">Explorer</div>
            <div class="file-tree">
              ${this.renderFileTree(this.files)}
            </div>
          </div>

          <div class="editor-area">
            <div class="tabs">
              ${this.tabs.map((tab) => html`
                <div
                  class="tab ${tab.id === this.activeTab ? 'active' : ''}"
                  @click=${() => (this.activeTab = tab.id)}
                >
                  <span>${tab.name}</span>
                  ${this.tabs.length > 1
                    ? html`<span class="tab-close" @click=${(e: Event) => { e.stopPropagation(); this.closeTab(tab.id); }}>×</span>`
                    : nothing}
                </div>
              `)}
            </div>

            <div class="editor-content">
              ${activeGuide
                ? html`<div class="guide-content" .innerHTML=${activeGuide.trim()}></div>`
                : html`<div class="code-view">No content</div>`}
            </div>
          </div>
        </div>

        <div class="terminal-panel">
          <div class="terminal-header">
            <span>Terminal</span>
          </div>
          <div class="terminal-container"></div>
        </div>
      </div>
    `
  }
}
