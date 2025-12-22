<template>
  <div class="columns">
    <div class="columns-left">
      <slot name="left" />
    </div>
    <div class="columns-right">
      <div class="columns-right-sticky">
        <slot name="right" />
      </div>
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
}

.columns-right-sticky {
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
  .columns-right-sticky {
    position: static;
  }
}
</style>
