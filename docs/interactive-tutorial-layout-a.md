---
layout: doc
class: interactive-tutorial
---

# Interactive Tutorial (Layout A)

<script setup>
// This page uses viewport-fixed terminal layout
</script>

Experience Skillet with **Layout A**: a viewport-fixed terminal that stays visible as you scroll through the tutorial steps below.

<ClientOnly>
  <skillet-scrolling-docs></skillet-scrolling-docs>
</ClientOnly>

<style>
/* Push content away from fixed terminal */
@media (min-width: 960px) {
  .interactive-tutorial .vp-doc {
    padding-right: calc(50% + 32px);
  }
}
</style>
