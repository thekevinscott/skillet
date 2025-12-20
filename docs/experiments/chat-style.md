---
layout: false
---

<script setup>
import { onMounted, ref } from 'vue'

const loaded = ref(false)
onMounted(() => { loaded.value = true })
</script>

<ClientOnly>
  <skillet-chat-tutorial v-if="loaded" style="height: 100vh;" />
</ClientOnly>

<style>
body {
  margin: 0;
  padding: 0;
  overflow: hidden;
}
.VPNav, .VPSidebar, .VPFooter, .VPDocFooter {
  display: none !important;
}
</style>
