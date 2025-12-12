import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'Skillet',
  description: 'Evaluation-driven Claude Code skill development',
  themeConfig: {
    nav: [
      { text: 'Home', link: '/' },
      { text: 'Getting Started', link: '/getting-started' }
    ],
    sidebar: [
      {
        text: 'Guide',
        items: [
          { text: 'Getting Started', link: '/getting-started' }
        ]
      }
    ]
  },
  vite: {
    server: {
      host: '0.0.0.0',
      port: 8001
    }
  }
})
