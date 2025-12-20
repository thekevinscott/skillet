import { SkilletCelebrationOverlay, TAG_NAME } from './celebration-overlay.js'

// Register the custom element
if (typeof window !== 'undefined' && !customElements.get(TAG_NAME)) {
  customElements.define(TAG_NAME, SkilletCelebrationOverlay)
}

export { SkilletCelebrationOverlay, TAG_NAME }
