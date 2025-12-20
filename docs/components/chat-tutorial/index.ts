import { SkilletChatTutorial, TAG_NAME } from './chat-tutorial.js'

if (!customElements.get(TAG_NAME)) {
  customElements.define(TAG_NAME, SkilletChatTutorial)
}

export { SkilletChatTutorial, TAG_NAME }
