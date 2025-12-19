import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'Skillet',
  description: 'Evaluation-driven Claude Code skill development',

  head: [
    ['link', { rel: 'icon', href: '/favicon.svg' }]
  ],

  themeConfig: {
    logo: '/favicon.svg',

    nav: [
      { text: 'Home', link: '/' },
      { text: 'Getting Started', link: '/getting-started' },
      { text: 'Interactive Tutorial', link: '/interactive-tutorial' }
    ],

    sidebar: [
      {
        text: 'Guide',
        items: [
          { text: 'Overview', link: '/' },
          { text: 'Getting Started', link: '/getting-started' },
          { text: 'Interactive Tutorial', link: '/interactive-tutorial' }
        ]
      }
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/thekevinscott/skillet' }
    ]
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
