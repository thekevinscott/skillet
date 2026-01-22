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

    // Left sidebar - organized navigation
    sidebar: [
      { text: 'Overview', link: '/' },
      { text: 'Getting Started', link: '/getting-started' },
      {
        text: 'Guides',
        items: [
          { text: 'Capture with /skillet:add', link: '/guides/capture-with-slash-command' }
        ]
      },
      {
        text: 'Reference',
        items: [
          { text: 'CLI', link: '/reference/cli' },
          { text: 'Eval Format', link: '/reference/eval-format' },
          { text: 'Python API', link: '/reference/python-api' }
        ]
      }
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

  vite: {
    server: {
      port: 5180,
      strictPort: true
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
