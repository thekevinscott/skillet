import { define } from '../utils/define.js'
import { TAG_NAME, SkilletUnifiedTerminal } from './unified-terminal.js'

export { TAG_NAME, SkilletUnifiedTerminal }

define(TAG_NAME, SkilletUnifiedTerminal)

declare global {
  interface HTMLElementTagNameMap {
    [TAG_NAME]: SkilletUnifiedTerminal
  }
}
