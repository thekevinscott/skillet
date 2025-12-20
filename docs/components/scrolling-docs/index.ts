import { SkilletScrollingDocs, TAG_NAME } from './scrolling-docs.js'

// Register the custom element
if (typeof window !== 'undefined' && !customElements.get(TAG_NAME)) {
  customElements.define(TAG_NAME, SkilletScrollingDocs)
}

export { SkilletScrollingDocs, TAG_NAME }
