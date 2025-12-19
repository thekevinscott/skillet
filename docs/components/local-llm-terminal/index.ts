import { define } from '../utils/define.js'
import { TAG_NAME, SkilletLocalLLMTerminal } from './local-llm-terminal.js'

export { TAG_NAME, SkilletLocalLLMTerminal }

define(TAG_NAME, SkilletLocalLLMTerminal)

declare global {
  interface HTMLElementTagNameMap {
    [TAG_NAME]: SkilletLocalLLMTerminal
  }
}
