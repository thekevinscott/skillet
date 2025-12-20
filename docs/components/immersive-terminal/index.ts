import { SkilletImmersiveTerminal, TAG_NAME } from './immersive-terminal.js'

if (typeof window !== 'undefined' && !customElements.get(TAG_NAME)) {
  customElements.define(TAG_NAME, SkilletImmersiveTerminal)
}

export { SkilletImmersiveTerminal, TAG_NAME }
