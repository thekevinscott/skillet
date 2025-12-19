import { define } from '../utils/define.js'
import { TAG_NAME, SkilletReactiveDocs } from './reactive-docs.js'

export { TAG_NAME, SkilletReactiveDocs }

define(TAG_NAME, SkilletReactiveDocs)

declare global {
  interface HTMLElementTagNameMap {
    [TAG_NAME]: SkilletReactiveDocs
  }
}
