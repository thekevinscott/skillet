import { SkilletIdeTutorial, TAG_NAME } from './ide-tutorial.js'

if (!customElements.get(TAG_NAME)) {
  customElements.define(TAG_NAME, SkilletIdeTutorial)
}

export { SkilletIdeTutorial, TAG_NAME }
