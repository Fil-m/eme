<template>
    <div class="eme-app-page">
        <div class="eme-app-header">
            <h1 class="eme-app-title">
                <span class="me-2">{{ appConfig.icon }}</span>
                {{ appConfig.name }}
            </h1>
            <button class="btn btn-sm btn-ghost-secondary" @click="$emit('close')">✕</button>
        </div>

        <!-- Custom App Tabs -->
        <ul class="nav nav-tabs mb-4" v-if="appConfig.modules.length > 1">
            <li class="nav-item" v-for="mod in availableModules" :key="mod.id">
                <a class="nav-link" :class="{active: activeTab === mod.id}" href="#"
                    @click.prevent="activeTab = mod.id">
                    {{ mod.icon }} {{ mod.label }}
                </a>
            </li>
        </ul>

        <!-- Module Switcher -->
        <div class="modular-content position-relative" style="min-height:400px;">
            <component 
                v-if="activeModuleObj && activeModuleObj.comp" 
                :is="activeModuleObj.comp" 
                :user="user" 
                :visiting-user="null" 
                :auth="auth"
                @visit-user="$emit('visit-user', $event)" 
                @generate-qr="$emit('generate-qr', $event)"
                @update-user-avatar="user.avatar = $event" 
                @refresh-user="$emit('refresh-user')"
                @close="$emit('close')">
            </component>
            
            <div v-else class="text-center py-5 module-placeholder">
                <div style="font-size:3rem;">📦</div>
                <div class="mt-2 fw-bold">Модуль завантажується або не знайдено</div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    props: ['user', 'auth', 'appConfig', 'systemSettings'],
    data() {
        return {
            activeTab: this.appConfig.modules[0] || '',
            fetchedPublishedModules: []
        }
    },
    mounted() {
        this.fetchPublishedModules();
    },
    computed: {
        allKnownModules() {
            const baseModules = [
                { id: 'profile', label: 'Профіль', icon: '👤', comp: 'eme-profile' },
                { id: 'feed', label: 'Стіна', icon: '📰', comp: 'eme-userwalllight' },
                { id: 'gallery', label: 'Галерея', icon: '🖼️', comp: 'eme-gallery' },
                { id: 'chat', label: 'Чат', icon: '💬', comp: 'eme-chat' },
                { id: 'network', label: 'Мережа', icon: '🌐', comp: 'eme-network' },
                { id: 'projects', label: 'Проєкти', icon: '📁', comp: 'eme-projects' },
                { id: 'tasks', label: 'Завдання', icon: '✅', comp: 'eme-vikunja' },
                { id: 'memos', label: 'Нотатки', icon: '📝', comp: 'eme-memos' },
                { id: 'bookmarks', label: 'Закладки', icon: '🔖', comp: 'eme-bookmarks' },
                { id: 'mafia', label: 'ШІ Мафія', icon: '🎭', comp: 'eme-mafia' },
                { id: 'omnitools', label: 'OmniTools', icon: '🧰', comp: 'eme-omni-tools' },
                { id: 'indexer', label: 'Індексатор', icon: '📤', comp: 'eme-indexer' },
                { id: 'aibuilder', label: 'AI App Builder', icon: '🤖', comp: 'eme-a-i-builder' }
            ];
            
            return [...baseModules, ...this.fetchedPublishedModules];
        },
        availableModules() {
            if (!this.appConfig || !this.appConfig.modules) return [];
            return this.appConfig.modules.map(modId => {
                return this.allKnownModules.find(km => km.id === modId) || { id: modId, label: modId, icon: '📦' };
            });
        },
        activeModuleObj() {
            return this.availableModules.find(m => m.id === this.activeTab);
        }
    },
    methods: {
        async fetchPublishedModules() {
            try {
                const res = await fetch('/api/settings/me/', { headers: this.auth() });
                if (res.ok) {
                    const data = await res.json();
                    if (data.published_modules) {
                        this.fetchedPublishedModules = data.published_modules;
                    }
                }
            } catch (e) {
                console.error("Failed to fetch published modules", e);
            }
        }
    },
    watch: {
        appConfig(newVal) {
            if (newVal && newVal.modules && newVal.modules.length > 0) {
                if (!newVal.modules.includes(this.activeTab)) {
                    this.activeTab = newVal.modules[0];
                }
            }
        }
    }
}
</script>

<style scoped>
.eme-app-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--tblr-border-color);
}

.eme-app-title {
    font-size: 1.4rem;
    font-weight: 800;
    margin: 0;
}

.module-placeholder {
    background: var(--tblr-card-bg);
    border: 1px dashed var(--tblr-border-color);
    border-radius: 12px;
    padding: 32px;
    color: var(--tblr-secondary);
}
</style>
