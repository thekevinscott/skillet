import { SkilletCinematicTutorial, TAG_NAME } from './cinematic-tutorial.js'

if (typeof window !== 'undefined' && !customElements.get(TAG_NAME)) {
  customElements.define(TAG_NAME, SkilletCinematicTutorial)
}

export { SkilletCinematicTutorial, TAG_NAME }
