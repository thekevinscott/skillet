import { defineConfig } from 'vitepress'
import container from 'markdown-it-container'

export default defineConfig({
  title: 'Skillet',
  description: 'Evaluation-driven Claude Code skill development',

  head: [
    ['link', { rel: 'icon', href: '/favicon.svg' }]
  ],

  markdown: {
    config: (md) => {
      // Register custom containers for two-column layout
      md.use(container, 'columns', {
        render: (tokens: any[], idx: number) => {
          return tokens[idx].nesting === 1 ? '<div class="columns">\n' : '</div>\n'
        }
      })
      md.use(container, 'left', {
        render: (tokens: any[], idx: number) => {
          return tokens[idx].nesting === 1 ? '<div class="left">\n' : '</div>\n'
        }
      })
      md.use(container, 'right', {
        render: (tokens: any[], idx: number) => {
          return tokens[idx].nesting === 1 ? '<div class="right">\n' : '</div>\n'
        }
      })
    }
  },

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
      { text: 'Interactive Tutorial', link: '/interactive-tutorial' },
      { text: 'Excel Formulas', link: '/examples/xlsx-formulas' }
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
