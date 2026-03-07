<template>
    <div class="eme-app-page">
        <div class="eme-app-header">
            <h1 class="eme-app-title">Налаштування</h1>
            <button class="btn btn-sm btn-ghost-secondary" @click="$emit('close')">✕</button>
        </div>

        <!-- Settings tabs -->
        <ul class="nav nav-tabs mb-4">
            <li class="nav-item">
                <a class="nav-link" :class="{active: settingsTab==='profile'}" href="#"
                    @click.prevent="settingsTab='profile'">👤 Профіль</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" :class="{active: settingsTab==='system'}" href="#"
                    @click.prevent="settingsTab='system'">🖥 Система</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" :class="{active: settingsTab==='builder'}" href="#"
                    @click.prevent="settingsTab='builder'; fetchCustomApps()">🛠 App Builder</a>
            </li>
        </ul>

        <!-- Profile tab -->
        <div v-if="settingsTab === 'profile'">
            <div class="card">
                <div class="card-body">
                    <div class="row g-3 mb-3">
                        <div class="col-md-6">
                            <label class="form-label">Ім'я</label>
                            <input type="text" class="form-control" v-model="user.first_name">
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Локація</label>
                            <input type="text" class="form-control" v-model="user.address">
                        </div>
                        <div class="col-12">
                            <label class="form-label">Про мене</label>
                            <textarea class="form-control" v-model="user.bio" rows="3"></textarea>
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">Дата народження</label>
                            <input type="date" class="form-control" v-model="user.birth_date">
                        </div>
                    </div>

                    <!-- Social links -->
                    <label class="form-label">Соцмережі</label>
                    <div v-for="(s, i) in user.social_links" :key="s.id"
                        class="d-flex align-items-center gap-2 mb-2 p-2 rounded"
                        style="background:rgba(255,255,255,.03);border:1px solid var(--tblr-border-color);">
                        <span class="fw-bold" style="min-width:80px;">{{ s.network_name }}</span>
                        <span class="text-muted flex-grow-1">{{ s.link }}</span>
                        <button class="btn btn-ghost-danger btn-sm btn-icon"
                            @click="deleteSocial(s.id, i)">✕</button>
                    </div>
                    <div class="row g-2 mt-1">
                        <div class="col-3">
                            <input type="text" class="form-control form-control-sm" v-model="newSocial.name"
                                placeholder="Telegram">
                        </div>
                        <div class="col-7">
                            <input type="text" class="form-control form-control-sm" v-model="newSocial.link"
                                placeholder="@username">
                        </div>
                        <div class="col-2">
                            <button class="btn btn-sm btn-outline-secondary w-100" @click="addSocial">+ Додати</button>
                        </div>
                    </div>

                    <div class="mt-4">
                        <button class="btn btn-primary" @click="saveProfile" :disabled="loading">
                            <span v-if="loading" class="spinner-border spinner-border-sm me-1"></span>
                            Зберегти зміни
                        </button>
                        <span v-if="saveSuccess" class="ms-3 text-success">✅ Збережено!</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- System tab -->
        <div v-if="settingsTab === 'system'">
            <div class="card">
                <div class="card-body">
                    <div class="mb-3">
                        <label class="form-label">Назва Ноди</label>
                        <input type="text" class="form-control" v-model="localSettings.node_name"
                            style="max-width:320px;">
                    </div>
                    <div class="mb-4">
                        <label class="form-label">Тема оформлення</label>
                        <select class="form-select" v-model="localSettings.theme" style="max-width:220px;">
                            <option value="dark">Dark Cyber</option>
                            <option value="light">Light Mesh</option>
                        </select>
                    </div>
                    <button class="btn btn-primary" @click="saveSystemSettings" :disabled="loading">
                        <span v-if="loading" class="spinner-border spinner-border-sm me-1"></span>
                        Зберегти
                    </button>
                    <span v-if="saveSuccess" class="ms-3 text-success">✅ Збережено!</span>
                    <hr class="my-4">
                    
                    <h3 class="card-title mb-3">Навігація (Dock)</h3>
                    <p class="text-muted small">Оберіть модулі, які будуть відображатися на вашій бічній панелі. Порядок збережеться автоматично.</p>
                    <div class="row g-2 mb-4">
                        <div class="col-md-4 col-sm-6" v-for="item in navItemsAvailable" :key="item.item_id">
                            <label class="form-check card card-radio p-3 border-0 bg-dark-lt h-100 mb-0">
                                <input class="form-check-input" type="checkbox" :value="item.item_id" v-model="localSettings.dock_apps">
                                <span class="form-check-label d-flex align-items-center gap-2">
                                    <span style="font-size: 1.2rem;">{{ item.icon }}</span>
                                    <span>{{ item.label }}</span>
                                </span>
                            </label>
                        </div>
                    </div>
                    <button class="btn btn-primary" @click="saveSystemSettings" :disabled="loading">
                        Зберегти Навігацію
                    </button>
                    
                    <hr class="my-4">
                    <h3 class="card-title mb-3">Мобільне розгортання</h3>
                    <p class="text-muted small">Скануйте QR-код або скопіюйте команду нижче, щоб швидко розгорнути EME OS на вашому Android пристрої через Termux.</p>
                    
                    <div class="row align-items-center g-3">
                        <div class="col-auto">
                            <div class="p-2 bg-white rounded shadow-sm" style="width:160px;height:160px;">
                                <img :src="qrUrl" alt="Termux Setup QR" style="width:100%;height:100%;">
                            </div>
                        </div>
                        <div class="col">
                            <div class="input-group mb-2">
                                <input type="text" class="form-control form-control-sm bg-dark text-info font-monospace" readonly :value="termuxCommand">
                                <button class="btn btn-sm btn-outline-info" @click="copyCommand">Копіювати</button>
                            </div>
                            <ol class="small text-muted ps-3 mb-0">
                                <li>Відкрийте <b>Termux</b> на телефоні.</li>
                                <li>Вставте скопійовану команду (або скануйте QR за посиланням).</li>
                                <li>Натисніть <b>Enter</b> та дочекайтеся завершення.</li>
                            </ol>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- App Builder tab -->
        <div v-if="settingsTab === 'builder'">
            <div class="card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h3 class="card-title m-0">Ваші Додатки (Custom Apps)</h3>
                    <button class="btn btn-primary btn-sm" @click="createNewApp">+ Створити</button>
                </div>
                <div class="card-body">
                    <p class="text-muted small mb-4">Тут ви можете збирати власні додатки з існуючих модулів (Microkernel Architecture).</p>
                    
                    <div v-if="editingApp" class="bg-dark-lt p-3 rounded mb-4 border border-primary">
                        <h5>{{ editingApp.id ? 'Редагувати додаток' : 'Новий додаток' }}</h5>
                        
                        <div v-if="!editingApp.id" class="mb-3">
                            <label class="form-label text-muted small">Швидкі пресети:</label>
                            <div class="d-flex flex-wrap gap-2">
                                <button v-for="p in appPresets" :key="p.id" 
                                    class="btn btn-sm btn-outline-info" 
                                    @click="applyPreset(p)">
                                    {{ p.icon }} {{ p.name }}
                                </button>
                            </div>
                        </div>

                        <div class="row g-2 mb-3">
                            <div class="col-md-2">
                                <label class="form-label">Іконка</label>
                                <input type="text" class="form-control" v-model="editingApp.icon" placeholder="📱">
                            </div>
                            <div class="col-md-10">
                                <label class="form-label">Назва (напр. "Моя Соцмережа")</label>
                                <input type="text" class="form-control" v-model="editingApp.name">
                            </div>
                        </div>
                        <label class="form-label">Оберіть модулі:</label>
                        <div class="row g-2 mb-3">
                            <div class="col-md-3 col-sm-4" v-for="mod in availableModulesForBuilder" :key="mod.id">
                                <label class="form-check card card-radio p-2 border-0 h-100 mb-0">
                                    <input class="form-check-input" type="checkbox" :value="mod.id" v-model="editingApp.modules">
                                    <span class="form-check-label d-flex align-items-center gap-2 small">
                                        <span>{{ mod.icon }}</span>
                                        <span>{{ mod.label }}</span>
                                    </span>
                                </label>
                            </div>
                        </div>
                        <div class="d-flex gap-2">
                            <button class="btn btn-primary" @click="saveCustomApp">Зберегти</button>
                            <button class="btn btn-ghost-secondary" @click="editingApp = null">Скасувати</button>
                        </div>
                    </div>

                    <div class="row g-3">
                        <div class="col-md-6" v-for="app in customApps" :key="app.id">
                            <div class="card shadow-sm border-0">
                                <div class="card-body p-3 d-flex align-items-start gap-3">
                                    <div class="avatar avatar-md bg-primary-lt" style="font-size: 1.5rem;">{{ app.icon || '📱' }}</div>
                                    <div class="flex-grow-1">
                                        <div class="fw-bold">{{ app.name }}</div>
                                        <div class="text-muted small mt-1">
                                            Модулі: 
                                            <span v-for="m in app.modules" :key="m" class="badge bg-secondary-lt me-1">{{ getModuleLabel(m) }}</span>
                                        </div>
                                    </div>
                                    <div class="dropdown">
                                        <button class="btn btn-ghost-secondary btn-icon btn-sm" data-bs-toggle="dropdown">⋮</button>
                                        <div class="dropdown-menu dropdown-menu-end">
                                            <a href="#" class="dropdown-item" @click.prevent="editCustomApp(app)">Редагувати</a>
                                            <a href="#" class="dropdown-item text-danger" @click.prevent="deleteCustomApp(app.id)">Видалити</a>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div v-if="!customApps.length && !editingApp" class="col-12 py-4 text-center text-muted border border-dashed rounded">
                            У вас ще немає створених додатків. Натисніть "Створити", щоб зібрати свою першу збірку.
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    props: ['user', 'systemSettings', 'auth', 'navItems'],
    data() {
        return {
            settingsTab: 'profile',
            loading: false,
            saveSuccess: false,
            newSocial: { name: '', link: '' },
            localSettings: { dock_apps: [], ...this.systemSettings },
            copySuccess: false,
            customApps: [],
            fetchedPublishedModules: [],
            editingApp: null,
            appPresets: [
                { id: 'social', name: 'Соціальна мережа', icon: '📱', modules: ['profile', 'feed', 'chat', 'gallery', 'network'] },
                { id: 'work', name: 'Робочий простір', icon: '💼', modules: ['projects', 'tasks', 'memos', 'bookmarks'] },
                { id: 'media', name: 'Медіа-центр', icon: '🎬', modules: ['gallery', 'omnitools'] },
            ]
        }
    },
    watch: {
        systemSettings: {
            deep: true,
            handler(nv) {
                this.localSettings = { ...nv };
                if (!this.localSettings.dock_apps || this.localSettings.dock_apps.length === 0) {
                    this.localSettings.dock_apps = ['desktop', 'apps_store', 'settings'];
                }
            }
        }
    },
    computed: {
        availableModulesForBuilder() {
            const baseModules = [
                { id: 'profile', label: 'Профіль', icon: '👤', comp: 'eme-profile' },
                { id: 'network', label: 'Мережа (Mesh)', icon: '🌐', comp: 'eme-network' },
                { id: 'chat', label: 'Чат', icon: '💬', comp: 'eme-chat' },
                { id: 'gallery', label: 'Галерея (Перегляд)', icon: '🖼️', comp: 'eme-gallery' },
                { id: 'indexer', label: 'Індексатор (Завантаження)', icon: '📤', comp: 'eme-indexer' },
                { id: 'projects', label: 'Проєкти', icon: '📁', comp: 'eme-projects' },
                { id: 'tasks', label: 'Завдання (Vikunja)', icon: '✅', comp: 'eme-vikunja' },
                { id: 'memos', label: 'Нотатки (Memos)', icon: '📝', comp: 'eme-memos' },
                { id: 'bookmarks', label: 'Закладки', icon: '🔖', comp: 'eme-bookmarks' },
                { id: 'mafia', label: 'ШІ Мафія', icon: '🎭', comp: 'eme-mafia' },
                { id: 'omnitools', label: 'OmniTools', icon: '🧰', comp: 'eme-omni-tools' },
                { id: 'feed', label: 'Стіна (У розробці)', icon: '📰', comp: 'eme-feed' },
                { id: 'aibuilder', label: 'AI App Builder', icon: '🤖', comp: 'eme-a-i-builder' },
            ];
            
            return [...baseModules, ...this.fetchedPublishedModules];
        },
        navItemsAvailable() {
            let items = [];
            if (this.navItems) {
                items = this.navItems.filter(i => !i.parent);
            }
            // Add custom apps to dock selection
            if (this.customApps && this.customApps.length > 0) {
                this.customApps.forEach(app => {
                    items.push({
                        item_id: 'custom_app_' + app.id,
                        label: app.name,
                        icon: app.icon || '📱'
                    });
                });
            }
            return items;
        },
        termuxCommand() {
            const ip = this.localSettings.server_ip || '127.0.0.1';
            return `curl -L http://${ip}:8080/bootstrap_eme.sh | bash -s -- ${ip}`;
        },
        qrUrl() {
            return `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(this.termuxCommand)}`;
        }
    },
    mounted() {
        this.fetchPublishedModules();
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
        },
        async saveProfile() {
            this.loading = true;
            try {
                const res = await fetch('/api/profiles/me/', {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json', ...this.auth() },
                    body: JSON.stringify(this.user)
                });
                if (res.ok) {
                    this.saveSuccess = true;
                    setTimeout(() => this.saveSuccess = false, 1500);
                    this.$emit('update:user', await res.json());
                }
            } catch (e) { } finally { this.loading = false; }
        },
        async addSocial() {
            if (!this.newSocial.name || !this.newSocial.link) return;
            try {
                const res = await fetch('/api/profiles/social-links/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', ...this.auth() },
                    body: JSON.stringify({
                        network_name: this.newSocial.name,
                        link: this.newSocial.link
                    })
                });
                if (res.ok) {
                    this.newSocial = { name: '', link: '' };
                    this.$emit('refresh-user');
                }
            } catch (e) { }
        },
        async deleteSocial(id) {
            try {
                const res = await fetch(`/api/profiles/social-links/${id}/`, {
                    method: 'DELETE',
                    headers: this.auth()
                });
                if (res.ok) this.$emit('refresh-user');
            } catch (e) { }
        },
        async saveSystemSettings() {
            this.loading = true;
            try {
                const res = await fetch('/api/settings/me/', {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json', ...this.auth() },
                    body: JSON.stringify(this.localSettings)
                });
                if (res.ok) {
                    this.saveSuccess = true;
                    setTimeout(() => this.saveSuccess = false, 1500);
                    this.$emit('update:system-settings', await res.json());
                }
            } catch (e) { } finally { this.loading = false; }
        },
        copyCommand() {
            navigator.clipboard.writeText(this.termuxCommand);
            alert('Команду скопійовано у буфер обміну!');
        },
        async fetchCustomApps() {
            try {
                const res = await fetch('/api/settings/apps/', { headers: this.auth() });
                const data = await res.json();
                this.customApps = data.results || data;
            } catch (e) { }
        },
        createNewApp() {
            this.editingApp = { name: '', icon: '📱', modules: [] };
        },
        applyPreset(p) {
            this.editingApp.name = p.name;
            this.editingApp.icon = p.icon;
            this.editingApp.modules = [...p.modules];
        },
        editCustomApp(app) {
            this.editingApp = { ...app };
        },
        async saveCustomApp() {
            if (!this.editingApp.name) return;
            try {
                const isNew = !this.editingApp.id;
                const method = isNew ? 'POST' : 'PATCH';
                const url = isNew ? '/api/settings/apps/' : `/api/settings/apps/${this.editingApp.id}/`;
                
                const res = await fetch(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json', ...this.auth() },
                    body: JSON.stringify(this.editingApp)
                });
                
                if (res.ok) {
                    this.editingApp = null;
                    await this.fetchCustomApps();
                    // emit an event to refresh nav if needed, but fetchCustomApps updates the local list which updates navItemsAvailable
                }
            } catch (e) { }
        },
        async deleteCustomApp(id) {
            if (!confirm('Видалити цей додаток?')) return;
            try {
                const res = await fetch(`/api/settings/apps/${id}/`, {
                    method: 'DELETE',
                    headers: this.auth()
                });
                if (res.ok) {
                    await this.fetchCustomApps();
                }
            } catch (e) { }
        },
        getModuleLabel(modId) {
            const m = this.availableModulesForBuilder.find(x => x.id === modId);
            return m ? m.label : modId;
        }
    },
    mounted() {
        this.fetchCustomApps();
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
    background: var(--eme-grad);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
}
</style>
