<script setup>
import { useSlots } from 'vue'
const slots = useSlots()
</script>

<template>
  <div class="columns">
    <div class="columns-left">
      <slot />
    </div>
    <div class="columns-right">
      <slot name="code" />
    </div>
  </div>
</template>

<style scoped>
.columns {
  display: flex;
  gap: 2rem;
  margin: 2rem 0;
}

.columns-left {
  flex: 1;
  min-width: 0;
}

.columns-right {
  width: 45%;
  position: relative;
}

.columns-right :deep(div) {
  position: sticky;
  top: 80px;
}

@media (max-width: 768px) {
  .columns {
    flex-direction: column;
  }
  .columns-right {
    width: 100%;
  }
  .columns-right :deep(div) {
    position: static;
  }
}
</style>
