import { LitElement, html, css, nothing } from 'lit'
import { property, state, query } from 'lit/decorators.js'
import { unsafeHTML } from 'lit/directives/unsafe-html.js'
import { Terminal as XTerm } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import { WebContainer } from '@webcontainer/api'

export const TAG_NAME = 'skillet-chat-tutorial'

interface Message {
  id: string
  type: 'assistant' | 'user' | 'system' | 'terminal'
  content: string
  timestamp: Date
  actions?: Action[]
}

interface Action {
  label: string
  command?: string
  nextStep?: number
}

/**
 * Chat-style tutorial that feels like messaging an AI assistant.
 * Messages appear conversationally, terminal embeds inline.
 */
export class SkilletChatTutorial extends LitElement {
  static styles = css`
    :host {
      display: block;
      height: 100%;
      min-height: 600px;
    }

    .chat {
      height: 100%;
      display: flex;
      flex-direction: column;
      background: linear-gradient(180deg, #0a0a0a 0%, #111 100%);
      border-radius: 12px;
      overflow: hidden;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }

    /* Header */
    .header {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 16px 20px;
      background: rgba(255, 255, 255, 0.03);
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    .avatar {
      width: 40px;
      height: 40px;
      border-radius: 12px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
    }

    .header-info {
      flex: 1;
    }

    .header-title {
      font-size: 16px;
      font-weight: 600;
      color: #fff;
    }

    .header-status {
      font-size: 12px;
      color: #4ade80;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #4ade80;
    }

    /* Messages area */
    .messages {
      flex: 1;
      overflow-y: auto;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .message {
      display: flex;
      gap: 12px;
      max-width: 85%;
      animation: fadeIn 0.3s ease-out;
    }

    @keyframes fadeIn {
      from {
        opacity: 0;
        transform: translateY(10px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    .message.assistant {
      align-self: flex-start;
    }

    .message.user {
      align-self: flex-end;
      flex-direction: row-reverse;
    }

    .message.system {
      align-self: center;
      max-width: 100%;
    }

    .message.terminal {
      align-self: stretch;
      max-width: 100%;
    }

    .message-avatar {
      width: 32px;
      height: 32px;
      border-radius: 8px;
      flex-shrink: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
    }

    .message.assistant .message-avatar {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }

    .message.user .message-avatar {
      background: #333;
    }

    .message-bubble {
      padding: 12px 16px;
      border-radius: 16px;
      line-height: 1.5;
    }

    .message.assistant .message-bubble {
      background: rgba(255, 255, 255, 0.08);
      color: #e5e5e5;
      border-bottom-left-radius: 4px;
    }

    .message.user .message-bubble {
      background: #667eea;
      color: #fff;
      border-bottom-right-radius: 4px;
    }

    .message.system .message-bubble {
      background: transparent;
      color: #888;
      font-size: 12px;
      text-align: center;
    }

    .message-bubble h1 {
      font-size: 18px;
      margin: 0 0 12px 0;
      color: #fff;
    }

    .message-bubble h2 {
      font-size: 15px;
      margin: 16px 0 8px 0;
      color: #a5b4fc;
    }

    .message-bubble p {
      margin: 0 0 12px 0;
    }

    .message-bubble p:last-child {
      margin-bottom: 0;
    }

    .message-bubble code {
      background: rgba(0, 0, 0, 0.3);
      padding: 2px 6px;
      border-radius: 4px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 13px;
      color: #c4b5fd;
    }

    .message-bubble pre {
      background: rgba(0, 0, 0, 0.4);
      padding: 12px;
      border-radius: 8px;
      margin: 12px 0;
      overflow-x: auto;
    }

    .message-bubble pre code {
      background: none;
      padding: 0;
      color: #e5e5e5;
    }

    /* Actions */
    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 12px;
    }

    .action-btn {
      padding: 8px 16px;
      background: rgba(102, 126, 234, 0.2);
      border: 1px solid rgba(102, 126, 234, 0.3);
      border-radius: 20px;
      color: #a5b4fc;
      font-size: 13px;
      cursor: pointer;
      transition: all 0.2s;
    }

    .action-btn:hover {
      background: rgba(102, 126, 234, 0.3);
      border-color: #667eea;
    }

    /* Terminal message */
    .terminal-embed {
      background: #000;
      border-radius: 12px;
      overflow: hidden;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .terminal-header-bar {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 10px 14px;
      background: #1a1a1a;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    .terminal-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
    }
    .terminal-dot.red { background: #ff5f56; }
    .terminal-dot.yellow { background: #ffbd2e; }
    .terminal-dot.green { background: #27c93f; }

    .terminal-title {
      flex: 1;
      text-align: center;
      font-size: 12px;
      color: #666;
    }

    .terminal-container {
      height: 200px;
    }

    /* Typing indicator */
    .typing {
      display: flex;
      gap: 12px;
      padding: 16px 20px;
    }

    .typing-dots {
      display: flex;
      gap: 4px;
      padding: 12px 16px;
      background: rgba(255, 255, 255, 0.08);
      border-radius: 16px;
    }

    .typing-dot {
      width: 8px;
      height: 8px;
      background: #667eea;
      border-radius: 50%;
      animation: bounce 1.4s ease-in-out infinite;
    }

    .typing-dot:nth-child(1) { animation-delay: 0s; }
    .typing-dot:nth-child(2) { animation-delay: 0.2s; }
    .typing-dot:nth-child(3) { animation-delay: 0.4s; }

    @keyframes bounce {
      0%, 60%, 100% { transform: translateY(0); }
      30% { transform: translateY(-6px); }
    }

    /* Input area */
    .input-area {
      display: flex;
      gap: 12px;
      padding: 16px 20px;
      background: rgba(255, 255, 255, 0.03);
      border-top: 1px solid rgba(255, 255, 255, 0.1);
    }

    .input-field {
      flex: 1;
      padding: 12px 16px;
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 24px;
      color: #fff;
      font-size: 14px;
      outline: none;
    }

    .input-field:focus {
      border-color: #667eea;
    }

    .input-field::placeholder {
      color: #666;
    }

    .send-btn {
      width: 44px;
      height: 44px;
      border-radius: 50%;
      background: #667eea;
      border: none;
      color: #fff;
      font-size: 18px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: transform 0.1s;
    }

    .send-btn:hover {
      transform: scale(1.05);
    }

    .send-btn:active {
      transform: scale(0.95);
    }

    /* Progress */
    .progress {
      display: flex;
      gap: 8px;
      padding: 8px 20px;
      background: rgba(255, 255, 255, 0.02);
    }

    .progress-step {
      flex: 1;
      height: 4px;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 2px;
      overflow: hidden;
    }

    .progress-step.completed {
      background: #667eea;
    }

    .progress-step.current::after {
      content: '';
      display: block;
      height: 100%;
      width: 50%;
      background: #667eea;
      animation: progress 2s ease-in-out infinite;
    }

    @keyframes progress {
      0% { width: 30%; }
      50% { width: 70%; }
      100% { width: 30%; }
    }
  `

  @state() private messages: Message[] = []
  @state() private isTyping = false
  @state() private currentStep = 0
  @state() private terminalReady = false
  @state() private userInput = ''

  @query('.terminal-container') private terminalContainer!: HTMLDivElement
  @query('.messages') private messagesContainer!: HTMLDivElement

  private xterm: XTerm | null = null
  private fitAddon: FitAddon | null = null
  private container: WebContainer | null = null
  private inputWriter: WritableStreamDefaultWriter | null = null

  private script: Array<{ assistant?: string; actions?: Action[] }> = [
    {
      assistant: `# Hey there! 👋

I'm your Skillet guide. I'll walk you through the basics of using this framework.

First, let me boot up a terminal for you. This is where you'll run commands throughout the tutorial.`,
      actions: [
        { label: '🚀 Start Terminal', command: '__boot_terminal__' },
      ],
    },
    {
      assistant: `Great! Your terminal is ready.

Let's start with something simple. Try running this command to see what files are in your workspace:

\`\`\`bash
ls -la
\`\`\``,
      actions: [
        { label: '▶️ Run: ls -la', command: 'ls -la' },
        { label: 'What does this do?', nextStep: -1 },
      ],
    },
    {
      assistant: `You can see there's a \`src\` folder with some files inside.

Now let's read the contents of a file:

\`\`\`bash
cat src/hello.txt
\`\`\``,
      actions: [
        { label: '▶️ Run: cat src/hello.txt', command: 'cat src/hello.txt' },
      ],
    },
    {
      assistant: `Nice! You're getting the hang of it.

Let's run some JavaScript. Node.js is available in your environment:

\`\`\`bash
node src/greeting.js
\`\`\``,
      actions: [
        { label: '▶️ Run: node src/greeting.js', command: 'node src/greeting.js' },
      ],
    },
    {
      assistant: `Now let's create something new! Use echo to write to a file:

\`\`\`bash
echo "I made this!" > myfile.txt
\`\`\``,
      actions: [
        { label: '▶️ Create the file', command: 'echo "I made this!" > myfile.txt' },
      ],
    },
    {
      assistant: `Let's verify your file was created:

\`\`\`bash
cat myfile.txt
\`\`\``,
      actions: [
        { label: '▶️ Read myfile.txt', command: 'cat myfile.txt' },
      ],
    },
    {
      assistant: `# 🎉 Congratulations!

You've completed the tutorial! You now know how to:
- Navigate files with \`ls\`
- Read files with \`cat\`
- Run JavaScript with \`node\`
- Create files with \`echo\`

Ready to build something real? Check out the [Getting Started](/getting-started) guide!`,
      actions: [
        { label: '🔄 Start Over', command: '__restart__' },
      ],
    },
  ]

  async firstUpdated() {
    // Start the conversation
    this.addSystemMessage('Today')
    await this.typeNextMessage()
  }

  private addSystemMessage(content: string) {
    this.messages = [
      ...this.messages,
      {
        id: `system-${Date.now()}`,
        type: 'system',
        content,
        timestamp: new Date(),
      },
    ]
  }

  private async typeNextMessage() {
    if (this.currentStep >= this.script.length) return

    this.isTyping = true
    await new Promise((r) => setTimeout(r, 1000))

    const step = this.script[this.currentStep]
    if (step.assistant) {
      this.messages = [
        ...this.messages,
        {
          id: `msg-${Date.now()}`,
          type: 'assistant',
          content: step.assistant,
          timestamp: new Date(),
          actions: step.actions,
        },
      ]
    }

    this.isTyping = false
    this.scrollToBottom()
  }

  private scrollToBottom() {
    requestAnimationFrame(() => {
      if (this.messagesContainer) {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight
      }
    })
  }

  private async handleAction(action: Action) {
    // Add user message showing the action taken
    this.messages = [
      ...this.messages,
      {
        id: `user-${Date.now()}`,
        type: 'user',
        content: action.label.replace(/^[^\s]+\s/, ''),
        timestamp: new Date(),
      },
    ]

    if (action.command === '__boot_terminal__') {
      await this.addTerminalMessage()
      await this.initTerminal()
    } else if (action.command === '__restart__') {
      this.messages = []
      this.currentStep = 0
      this.addSystemMessage('Restarting tutorial...')
      await this.typeNextMessage()
      return
    } else if (action.command) {
      await this.runCommand(action.command)
    }

    if (action.nextStep !== undefined) {
      this.currentStep = action.nextStep
    } else {
      this.currentStep++
    }

    await this.typeNextMessage()
  }

  private async addTerminalMessage() {
    this.messages = [
      ...this.messages,
      {
        id: `terminal-${Date.now()}`,
        type: 'terminal',
        content: '',
        timestamp: new Date(),
      },
    ]
    await this.updateComplete
    this.scrollToBottom()
  }

  private async initTerminal() {
    await this.updateComplete

    if (!this.terminalContainer) return

    this.xterm = new XTerm({
      cursorBlink: true,
      fontSize: 13,
      fontFamily: '"JetBrains Mono", Menlo, Monaco, monospace',
      theme: {
        background: '#000',
        foreground: '#e5e5e5',
      },
    })

    this.fitAddon = new FitAddon()
    this.xterm.loadAddon(this.fitAddon)
    this.xterm.open(this.terminalContainer)
    this.fitAddon.fit()

    this.xterm.writeln('\x1b[90m⏳ Booting environment...\x1b[0m')

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
      }).observe(this.terminalContainer)

      this.terminalReady = true
      this.xterm.write('\r\x1b[K\x1b[32m✓ Ready!\x1b[0m\n\n')
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
    await new Promise((r) => setTimeout(r, 500))
  }

  private handleInputKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter' && this.userInput.trim()) {
      this.sendUserMessage()
    }
  }

  private sendUserMessage() {
    if (!this.userInput.trim()) return

    this.messages = [
      ...this.messages,
      {
        id: `user-${Date.now()}`,
        type: 'user',
        content: this.userInput,
        timestamp: new Date(),
      },
    ]

    // If terminal is ready, run as command
    if (this.terminalReady) {
      this.runCommand(this.userInput)
    }

    this.userInput = ''
    this.scrollToBottom()
  }

  private renderMessage(msg: Message) {
    if (msg.type === 'terminal') {
      return html`
        <div class="message terminal">
          <div class="terminal-embed">
            <div class="terminal-header-bar">
              <span class="terminal-dot red"></span>
              <span class="terminal-dot yellow"></span>
              <span class="terminal-dot green"></span>
              <span class="terminal-title">bash</span>
            </div>
            <div class="terminal-container"></div>
          </div>
        </div>
      `
    }

    if (msg.type === 'system') {
      return html`
        <div class="message system">
          <div class="message-bubble">${msg.content}</div>
        </div>
      `
    }

    return html`
      <div class="message ${msg.type}">
        <div class="message-avatar">
          ${msg.type === 'assistant' ? '🍳' : '👤'}
        </div>
        <div class="message-bubble">
          ${unsafeHTML(this.formatContent(msg.content))}
          ${msg.actions?.length
            ? html`
                <div class="actions">
                  ${msg.actions.map(
                    (action) => html`
                      <button class="action-btn" @click=${() => this.handleAction(action)}>
                        ${action.label}
                      </button>
                    `
                  )}
                </div>
              `
            : nothing}
        </div>
      </div>
    `
  }

  private formatContent(content: string): string {
    // Simple markdown formatting
    return content
      .replace(/^# (.+)$/gm, '<h1>$1</h1>')
      .replace(/^## (.+)$/gm, '<h2>$1</h2>')
      .replace(/\n\n/g, '</p><p>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" style="color: #a5b4fc;">$1</a>')
  }

  render() {
    const totalSteps = this.script.length
    const progress = Math.min(this.currentStep, totalSteps - 1)

    return html`
      <div class="chat">
        <div class="header">
          <div class="avatar">🍳</div>
          <div class="header-info">
            <div class="header-title">Skillet Guide</div>
            <div class="header-status">
              <span class="status-dot"></span>
              Online
            </div>
          </div>
        </div>

        <div class="progress">
          ${this.script.map(
            (_, i) => html`
              <div
                class="progress-step ${i < progress ? 'completed' : ''} ${i === progress ? 'current' : ''}"
              ></div>
            `
          )}
        </div>

        <div class="messages">
          ${this.messages.map((msg) => this.renderMessage(msg))}
          ${this.isTyping
            ? html`
                <div class="typing">
                  <div class="message-avatar" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                    🍳
                  </div>
                  <div class="typing-dots">
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                  </div>
                </div>
              `
            : nothing}
        </div>

        <div class="input-area">
          <input
            type="text"
            class="input-field"
            placeholder="${this.terminalReady ? 'Type a command...' : 'Chat with the guide...'}"
            .value=${this.userInput}
            @input=${(e: InputEvent) => (this.userInput = (e.target as HTMLInputElement).value)}
            @keydown=${this.handleInputKeydown}
          />
          <button class="send-btn" @click=${this.sendUserMessage}>↑</button>
        </div>
      </div>
    `
  }
}
