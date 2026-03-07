<template>
  <div class="eme-iframe-container h-100 w-100 d-flex flex-column">
    <header class="p-3 bg-dark border-bottom border-secondary d-flex justify-content-between align-items-center">
        <div class="d-flex align-items-center gap-3">
            <div class="header-icon-box" style="background: linear-gradient(135deg, #198754, #20c997);">✅</div>
            <div>
                <h3 class="m-0 text-white">Vikunja</h3>
                <span class="text-muted small">Управління завданнями (Повна заміна Projects)</span>
            </div>
        </div>
        <div class="d-flex gap-2">
            <button class="btn btn-outline-info" @click="openExternal">Відкрити в новому вікні ↗</button>
            <button class="btn btn-ghost-secondary" @click="$emit('close')">✕</button>
        </div>
    </header>
    <div v-if="hasError" class="flex-grow-1 d-flex flex-column justify-content-center align-items-center bg-black text-center p-5">
        <div class="fs-1 mb-3">🐳</div>
        <h3 class="text-danger">Контейнер не запущено</h3>
        <p class="text-muted max-w-lg">Vikunja працює як Docker-контейнер. Запустіть <code>docker-compose up -d</code> у папці <code>homelab</code>.</p>
        <button class="btn btn-primary mt-3" @click="retryLoad">Спробувати знову</button>
    </div>
    <iframe v-show="!hasError" ref="appFrame" :src="appUrl" class="flex-grow-1 border-0 w-100 bg-black"></iframe>
  </div>
</template>

<script>
export default {
    props: ['user', 'auth'],
    data() {
        return {
            appUrl: 'http://localhost:3456',
            hasError: false
        }
    },
    methods: {
        openExternal() {
            window.open(this.appUrl, '_blank');
        },
        retryLoad() {
            this.hasError = false;
            if (this.$refs.appFrame) {
                this.$refs.appFrame.src = this.appUrl;
            }
        }
    }
}
</script>

<style scoped>
.header-icon-box {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
}
.max-w-lg { max-width: 500px; margin: 0 auto; }
</style>
