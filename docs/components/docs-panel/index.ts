import { define } from '../utils/define.js'
import { TAG_NAME, SkilletDocsPanel } from './docs-panel.js'

export { TAG_NAME, SkilletDocsPanel }

define(TAG_NAME, SkilletDocsPanel)

declare global {
  interface HTMLElementTagNameMap {
    [TAG_NAME]: SkilletDocsPanel
  }
}
