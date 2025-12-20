import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'Skillet',
  description: 'Evaluation-driven Claude Code skill development',

  head: [
    ['link', { rel: 'icon', href: '/favicon.svg' }]
  ],

  themeConfig: {
    logo: '/favicon.svg',

    // Search
    search: {
      provider: 'local'
    },

    // Minimal top nav like agentskills.io
    nav: [
      { text: 'GitHub', link: 'https://github.com/thekevinscott/skillet' }
    ],

    // Left sidebar - flat navigation
    sidebar: [
      { text: 'Overview', link: '/' },
      { text: 'Getting Started', link: '/getting-started' },
      { text: 'Interactive Tutorial', link: '/interactive-tutorial' }
    ],

    // Right sidebar - "On this page" outline
    outline: {
      level: [2, 3],
      label: 'On this page'
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/thekevinscott/skillet' }
    ],

    // Footer
    footer: {
      message: 'Released under the MIT License.',
      copyright: 'Copyright © 2024-present'
    }
  },

  vue: {
    template: {
      compilerOptions: {
        // Treat tags starting with 'skillet-' as custom elements
        isCustomElement: (tag) => tag.startsWith('skillet-')
      }
    }
  }
})
