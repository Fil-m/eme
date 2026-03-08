<template>
    <div class="eme-app-page p-4">
        <div class="d-flex align-items-center mb-4">
            <span style="font-size:2rem; margin-right: 15px;">🧩</span>
            <h1 class="m-0" style="color: #00e5ff;">Додатки</h1>
            <button class="btn btn-sm btn-outline-success ms-3 d-flex align-items-center" @click="syncGit" :disabled="isSyncing">
                <span v-if="isSyncing" class="spinner-border spinner-border-sm me-1"></span>
                <span v-else>🔄 Оновити</span>
            </button>
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
                    <a href="#" class="list-group-item list-group-item-action" 
                       :class="{ active: currentCategory === 'productivity' }" 
                       @click.prevent="currentCategory = 'productivity'">
                        🚀 Продуктивність
                    </a>
                    <a href="#" class="list-group-item list-group-item-action" 
                       :class="{ active: currentCategory === 'media' }" 
                       @click.prevent="currentCategory = 'media'">
                        🖼️ Медіа
                    </a>
                    <a href="#" class="list-group-item list-group-item-action" 
                       :class="{ active: currentCategory === 'ai_apps' }" 
                       @click.prevent="currentCategory = 'ai_apps'">
                        ✨ Мої ШІ Додатки
                    </a>
                </div>
            </div>

            <!-- Apps Grid -->
            <div class="col-md-9">
                <div v-if="isLoading" class="text-center py-5">
                    <div class="spinner-border text-primary"></div>
                    <div class="mt-2 text-muted">Завантаження...</div>
                </div>
                <div v-else class="row row-cards">
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
                                
                                <!-- Management Actions for AI Apps -->
                                <div v-if="app.category === 'ai_apps'" class="mt-3 d-flex gap-2" @click.stop>
                                    <button class="btn btn-sm btn-outline-info" :disabled="isPushingAppId === app.id" @click="pushToGit(app)" title="Push to Git">
                                        <span v-if="isPushingAppId === app.id" class="spinner-border spinner-border-sm"></span>
                                        <span v-else>☁️</span>
                                    </button>
                                    <button class="btn btn-sm btn-outline-primary flex-grow-1" @click="editApp(app)">
                                        ✏️ Редагувати
                                    </button>
                                    <button class="btn btn-sm btn-outline-danger" @click.stop="deleteApp(app)">
                                        🗑️
                                    </button>
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
            currentCategory: 'all',
            isLoading: false,
            isSyncing: false,
            isPushingAppId: null,
            apps: []
        };
    },
    mounted() {
        this.fetchApps();
    },
    computed: {
        filteredApps() {
            if (this.currentCategory === 'all') return this.apps;
            return this.apps.filter(a => a.category === this.currentCategory);
        }
    },
    methods: {
        async fetchApps() {
            this.isLoading = true;
            try {
                const res = await fetch('/api/settings/available-apps/', { headers: this.auth() });
                if (res.ok) {
                    this.apps = await res.json();
                }
            } catch (e) {
                console.error("Failed to fetch apps", e);
            }
            this.isLoading = false;
        },
        async syncGit() {
            await this.$root.syncGit();
            this.fetchApps();
        },
        launchApp(app) {
            this.$root.activeApp = app.id;
        },
        editApp(app) {
            if (!app.draft_id) return;
            this.$root.editorDraftId = app.draft_id;
            this.$root.isEditorOpen = true;
        },
        async deleteApp(app) {
            if (!app.draft_id) return;
            if (!confirm(`Видалити додаток "${app.name}"?`)) return;
            
            try {
                const res = await fetch(`/api/settings/ai-builder/delete/${app.draft_id}/`, {
                    method: 'DELETE',
                    headers: this.auth()
                });
                if (res.ok) {
                    this.fetchApps();
                } else {
                    const err = await res.json();
                    alert(err.error || "Помилка видалення");
                }
            } catch (e) {
                alert("Помилка мережі.");
            }
        },
        async pushToGit(app) {
            if (!app.draft_id) return;
            this.isPushingAppId = app.id;
            try {
                const res = await fetch(`/api/settings/ai-builder/push/${app.draft_id}/`, {
                    method: 'POST',
                    headers: this.auth()
                });
                
                if (res.ok) {
                    const data = await res.json();
                    alert(data.message || "Додаток успішно відправлено в Git!");
                } else {
                    const error = await res.json();
                    alert(error.error || "Помилка відправки в Git");
                }
            } catch (e) {
                alert("Помилка підключення до сервера.");
            }
            this.isPushingAppId = null;
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
