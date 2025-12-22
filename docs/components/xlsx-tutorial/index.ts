import { SkilletXlsxTutorial, TAG_NAME } from './xlsx-tutorial-v2.js'

if (!customElements.get(TAG_NAME)) {
  customElements.define(TAG_NAME, SkilletXlsxTutorial)
}

export { SkilletXlsxTutorial, TAG_NAME }
