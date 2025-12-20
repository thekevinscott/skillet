<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import DefaultTheme from 'vitepress/theme'
import { useRoute } from 'vitepress'

const { Layout } = DefaultTheme

// Only show fixed terminal on tutorial pages
const route = useRoute()
const showFixedTerminal = ref(false)
const isTerminalReady = ref(false)
const terminalComponent = ref<HTMLElement | null>(null)

// Track if we're scrolling from clicking a step
const isAutoScrolling = ref(false)

// Tutorial state managed via custom events
const currentStep = ref(0)

function checkRoute() {
  // Enable fixed terminal layout on interactive tutorial page
  showFixedTerminal.value = route.path.includes('interactive-tutorial')
}

function handleTerminalReady() {
  isTerminalReady.value = true
}

function handleStepClick(stepIndex: number) {
  currentStep.value = stepIndex
  // Scroll to the step element
  const stepEl = document.querySelector(`[data-step-index="${stepIndex}"]`)
  if (stepEl) {
    isAutoScrolling.value = true
    stepEl.scrollIntoView({ behavior: 'smooth', block: 'start' })
    setTimeout(() => {
      isAutoScrolling.value = false
    }, 1000)
  }
}

onMounted(() => {
  checkRoute()

  // Listen for terminal ready events from the web component
  window.addEventListener('terminal-ready', handleTerminalReady)
})

onUnmounted(() => {
  window.removeEventListener('terminal-ready', handleTerminalReady)
})

watch(() => route.path, checkRoute)
</script>

<template>
  <Layout>
    <!-- Default content slot -->
    <template #doc-after>
      <!-- Fixed terminal pane for tutorial pages -->
      <div v-if="showFixedTerminal" class="fixed-terminal-wrapper">
        <div class="terminal-header">
          <span class="terminal-title">Terminal</span>
          <span class="terminal-status" :class="{ ready: isTerminalReady }">
            {{ isTerminalReady ? 'Ready' : 'Booting...' }}
          </span>
        </div>
        <div class="terminal-content">
          <skillet-terminal
            ref="terminalComponent"
            height="100%"
            @terminal-ready="handleTerminalReady"
          ></skillet-terminal>
        </div>
      </div>
    </template>
  </Layout>
</template>

<style scoped>
.fixed-terminal-wrapper {
  position: fixed;
  right: 0;
  top: var(--vp-nav-height, 64px);
  width: 50%;
  max-width: 700px;
  min-width: 400px;
  height: calc(100vh - var(--vp-nav-height, 64px));
  background: #1a1a1a;
  border-left: 1px solid var(--vp-c-border);
  display: flex;
  flex-direction: column;
  z-index: 20;
}

.terminal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #252525;
  border-bottom: 1px solid #333;
}

.terminal-title {
  font-size: 13px;
  font-weight: 600;
  color: #d4d4d4;
}

.terminal-status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  background: #333;
  color: #888;
}

.terminal-status.ready {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.terminal-content {
  flex: 1;
  min-height: 0;
}

/* Adjust main content when terminal is visible */
@media (min-width: 960px) {
  :global(.interactive-tutorial .VPDoc .content-container) {
    max-width: calc(50% - 32px) !important;
    margin-right: auto !important;
  }
}

/* Hide terminal on mobile */
@media (max-width: 959px) {
  .fixed-terminal-wrapper {
    display: none;
  }
}
</style>
