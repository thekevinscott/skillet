import { define } from '../utils/define.js'
import { TAG_NAME, SkilletApiKeyInput } from './api-key-input.js'

export { TAG_NAME, SkilletApiKeyInput }

define(TAG_NAME, SkilletApiKeyInput)

declare global {
  interface HTMLElementTagNameMap {
    [TAG_NAME]: SkilletApiKeyInput
  }
}
