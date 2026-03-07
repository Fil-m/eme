<template>
    <div class="eme-dashboard p-4">
        <header class="dashboard-header mb-4">
            <h1 class="greeting">Оболонка <span>{{ user.username || 'Користувач' }}</span></h1>
            <p class="text-muted">Персональний дашборд EME OS</p>
        </header>

        <div class="widget-grid">
            <!-- Clock Widget -->
            <div class="widget-container">
                <eme-widget-clock></eme-widget-clock>
            </div>
            
            <!-- Quick Links / Shortcuts -->
            <div class="widget-container">
                <div class="widget-card shortcuts-widget">
                    <h3>Швидкий доступ</h3>
                    <div class="d-flex flex-wrap gap-2 mt-3">
                        <button v-for="item in navItems.slice(0, 4)" :key="item.item_id" 
                                class="btn btn-dark" @click="$emit('open-app', item.item_id)">
                            {{ item.icon }} {{ item.label }}
                        </button>
                    </div>
                </div>
            </div>

            <!-- SysMon Widget -->
            <div class="widget-container" style="grid-column: span 2;">
                <div class="widget-card p-0 overflow-hidden d-flex flex-column">
                    <div class="bg-dark p-2 border-bottom border-secondary d-flex align-items-center">
                        <span class="fs-4 me-2">📈</span>
                        <h4 class="m-0 text-white">Моніторинг</h4>
                    </div>
                    <div class="p-3 flex-grow-1">
                        <eme-sys-mon :user="user" :auth="auth" :is-widget="true" @open-app="$emit('open-app', $event)"></eme-sys-mon>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    props: ['user', 'auth', 'navItems'],
    data() {
        return {
            layout: []
        }
    }
}
</script>

<style scoped>
.eme-dashboard {
    width: 100%;
    height: 100%;
    color: white;
    overflow-y: auto;
}

.greeting {
    font-size: 2rem;
    font-weight: 800;
    margin-bottom: 0.2rem;
}

.greeting span {
    background: var(--eme-grad);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.widget-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;
    grid-auto-rows: minmax(150px, auto);
}

.widget-card {
    background: rgba(26, 28, 46, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    padding: 20px;
    height: 100%;
    backdrop-filter: blur(10px);
    transition: transform 0.3s ease, border-color 0.3s ease;
}

.widget-card:hover {
    transform: translateY(-2px);
    border-color: rgba(0, 229, 255, 0.3);
}

.widget-card h3 {
    font-size: 1.1rem;
    margin: 0;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.9);
}

.empty-widget {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    border: 1px dashed rgba(255, 255, 255, 0.2);
    background: rgba(0, 0, 0, 0.2);
}

.empty-widget .icon {
    font-size: 2rem;
    margin-bottom: 10px;
    opacity: 0.5;
}
</style>
