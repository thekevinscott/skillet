---
title: "Excel Formulas - Use Case Walkthrough"
---

<script setup>
import { onMounted, ref } from 'vue'

const loaded = ref(false)
onMounted(() => { loaded.value = true })
</script>

<ClientOnly>
  <skillet-xlsx-tutorial v-if="loaded" />
</ClientOnly>

<style>
/* Keep nav visible but hide sidebar and doc chrome */
.VPSidebar, .VPDocFooter {
  display: none !important;
}
.VPDoc {
  padding: 0 !important;
}
.VPDoc .container {
  max-width: 100% !important;
}
.VPContent {
  padding: 0 !important;
}
</style>
