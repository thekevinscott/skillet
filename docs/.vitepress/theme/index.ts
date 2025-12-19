import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'
import './custom.css'

export default {
  extends: DefaultTheme,
  async enhanceApp() {
    // Only run in browser (not during SSR)
    if (typeof window !== 'undefined') {
      // Dynamically import components to register custom elements
      await import('../../components/terminal/index.js')
      await import('../../components/docs-panel/index.js')
      await import('../../components/reactive-docs/index.js')
      await import('../../components/api-key-input/index.js')
      await import('../../components/claude-terminal/index.js')
      await import('../../components/local-llm-terminal/index.js')
      await import('../../components/unified-terminal/index.js')
    }
  }
} satisfies Theme
