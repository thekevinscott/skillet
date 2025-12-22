import { SkilletUseCaseLayout, TAG_NAME } from './use-case-layout.js'

if (!customElements.get(TAG_NAME)) {
  customElements.define(TAG_NAME, SkilletUseCaseLayout)
}

export { SkilletUseCaseLayout, TAG_NAME }
