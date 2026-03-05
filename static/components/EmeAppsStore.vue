<template>
    <div class="eme-app-page p-4">
        <div class="d-flex align-items-center mb-4">
            <span style="font-size:2rem; margin-right: 15px;">🧩</span>
            <h1 class="m-0" style="color: #00e5ff;">Додатки</h1>
            <button class="btn btn-sm btn-ghost-secondary ms-auto" @click="$emit('close')">✕</button>
        </div>

        <div class="row">
            <!-- Sidebar / Categories -->
            <div class="col-md-3">
                <div class="list-group list-group-transparent">
                    <a href="#" class="list-group-item list-group-item-action" 
                       :class="{ active: currentCategory === 'all' }" 
                       @click.prevent="currentCategory = 'all'">
                        Усі додатки
                    </a>
                    <a href="#" class="list-group-item list-group-item-action" 
                       :class="{ active: currentCategory === 'games' }" 
                       @click.prevent="currentCategory = 'games'">
                        🎮 Ігри
                    </a>
                    <a href="#" class="list-group-item list-group-item-action" 
                       :class="{ active: currentCategory === 'utils' }" 
                       @click.prevent="currentCategory = 'utils'">
                        🔧 Утиліти
                    </a>
                </div>
            </div>

            <!-- Apps Grid -->
            <div class="col-md-9">
                <div class="row row-cards">
                    <!-- App Card -->
                    <div class="col-md-4 col-sm-6" v-for="app in filteredApps" :key="app.id">
                        <div class="card card-sm" style="background: var(--tblr-card-bg); border: 1px solid var(--tblr-border-color); border-radius: 12px; cursor: pointer; transition: transform 0.2s;" @click="launchApp(app)" :title="'Запустити ' + app.name">
                            <div class="card-body">
                                <div class="d-flex align-items-center">
                                    <span class="avatar avatar-md me-3" :style="{ background: app.color, color: 'white' }">{{ app.icon }}</span>
                                    <div>
                                        <div class="font-weight-medium" style="font-size: 1.1rem; color: #fff;">{{ app.name }}</div>
                                        <div class="text-muted" style="font-size: 0.85rem;">{{ app.developer }}</div>
                                    </div>
                                </div>
                                <div class="mt-3 text-muted" style="font-size: 0.9rem;">
                                    {{ app.description }}
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div v-if="filteredApps.length === 0" class="col-12 text-center py-5 text-muted">
                        У цій категорії поки немає додатків.
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    props: ['user', 'auth'],
    emits: ['close'],
    data() {
        return {
            currentCategory: 'games',
            apps: [
                {
                    id: 'park_adventures',
                    category: 'games',
                    name: 'Парк',
                    description: 'Інтерактивна гра з QR-сканером, битвами та будівництвом.',
                    icon: '🐉',
                    color: '#4ca528',
                    developer: 'EME Community'
                }
            ]
        };
    },
    computed: {
        filteredApps() {
            if (this.currentCategory === 'all') return this.apps;
            return this.apps.filter(a => a.category === this.currentCategory);
        }
    },
    methods: {
        launchApp(app) {
            this.$root.activeApp = app.id;
        }
    }
}
</script>

<style scoped>
.list-group-item {
    border: none;
    border-radius: 8px;
    margin-bottom: 5px;
    color: var(--tblr-secondary);
}
.list-group-item.active {
    background: rgba(0, 229, 255, 0.1);
    color: #00e5ff;
    font-weight: 600;
}
.list-group-item:hover:not(.active) {
    background: rgba(255, 255, 255, 0.05);
    color: white;
}
.card:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 20px rgba(0,0,0,0.3);
}
</style>
