import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'

// Import Lit components (will be created)
// These are auto-registered as custom elements

export default {
  extends: DefaultTheme,
  async enhanceApp({ app }) {
    // Only run in browser (not during SSR)
    if (typeof window !== 'undefined') {
      // Dynamically import components to avoid SSR issues
      await import('../../components/terminal')
      await import('../../components/docs-panel')
      await import('../../components/reactive-docs')
      await import('../../components/api-key-input')
      await import('../../components/claude-terminal')
      await import('../../components/local-llm-terminal')
      await import('../../components/unified-terminal')
    }
  }
} satisfies Theme
