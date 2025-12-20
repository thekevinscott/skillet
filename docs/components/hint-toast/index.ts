import { SkilletHintToast, TAG_NAME } from './hint-toast.js'

// Register the custom element
if (typeof window !== 'undefined' && !customElements.get(TAG_NAME)) {
  customElements.define(TAG_NAME, SkilletHintToast)
}

export { SkilletHintToast, TAG_NAME }
