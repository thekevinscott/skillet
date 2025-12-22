---
layout: false
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
html, body {
  margin: 0;
  padding: 0;
  overflow-x: hidden;
}
.VPNav, .VPSidebar, .VPFooter, .VPDocFooter, .VPDoc {
  display: none !important;
}
</style>
