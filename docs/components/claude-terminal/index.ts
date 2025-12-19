import { define } from '../utils/define.js'
import { TAG_NAME, SkilletClaudeTerminal } from './claude-terminal.js'

export { TAG_NAME, SkilletClaudeTerminal }

define(TAG_NAME, SkilletClaudeTerminal)

declare global {
  interface HTMLElementTagNameMap {
    [TAG_NAME]: SkilletClaudeTerminal
  }
}
