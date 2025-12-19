import { define } from '../utils/define.js'
import { TAG_NAME, SkilletTerminal } from './terminal.js'

export { TAG_NAME, SkilletTerminal }

define(TAG_NAME, SkilletTerminal)

declare global {
  interface HTMLElementTagNameMap {
    [TAG_NAME]: SkilletTerminal
  }
}
