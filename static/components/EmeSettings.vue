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
                    @click.prevent="settingsTab='builder'; fetchCustomApps(); fetchPublishedModules()">🛠 App Builder</a>
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
                    <p class="text-muted small">Перетягуйте або використовуйте стрілки, щоб змінити порядок додатків на бічній панелі. Тільки обрані відображаються.</p>
                    
                    <div class="list-group mb-4 border-0">
                        <div v-for="(item, idx) in sortedDockItems" :key="item.item_id" 
                            class="list-group-item bg-dark-lt d-flex align-items-center gap-3 mb-2 rounded border-primary-lt p-3"
                            :class="{'opacity-50': !localSettings.dock_apps.includes(item.item_id)}"
                            style="border:1px solid rgba(0, 229, 255, 0.1) !important;">
                            
                            <div class="form-check m-0">
                                <input class="form-check-input" type="checkbox" :value="item.item_id" v-model="localSettings.dock_apps">
                            </div>

                            <div class="flex-grow-1 d-flex flex-column">
                                <div class="d-flex align-items-center gap-2">
                                    <span style="font-size: 1.5rem;">{{ item.icon }}</span>
                                    <span class="fw-bold text-white fs-4">{{ item.label }}</span>
                                    <span v-if="item.isCustom" class="badge bg-purple-lt ms-2">Мій додаток</span>
                                </div>
                                <div v-if="item.description" class="text-muted small opacity-75">{{ item.description }}</div>
                            </div>

                            <div class="d-flex gap-1" v-if="localSettings.dock_apps.includes(item.item_id)">
                                <button class="btn btn-sm btn-ghost-info btn-icon" @click="moveDockItem(item.item_id, -1)" :disabled="idx === 0">↑</button>
                                <button class="btn btn-sm btn-ghost-info btn-icon" @click="moveDockItem(item.item_id, 1)" :disabled="idx === sortedDockItems.length - 1">↓</button>
                            </div>
                        </div>
                    </div>

                    <button class="btn btn-primary btn-lg shadow-sm" @click="saveSystemSettings" :disabled="loading">
                        Зберегти налаштування панелі
                    </button>
                    

                </div>
            </div>
        </div>

        <!-- App Builder tab -->
        <div v-if="settingsTab === 'builder'">
            <div class="alert alert-info py-2 small d-flex justify-content-between align-items-center mb-3">
                <span>Виявлено {{ publishedCount }} ШІ-модулів.</span>
                <button class="btn btn-sm btn-ghost-info" @click="fetchPublishedModules">🔄 Оновити список</button>
            </div>
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

                        <div class="row g-2 mb-3 align-items-end">
                            <div class="col-md-4">
                                <label class="form-label">Назва додатка</label>
                                <input type="text" class="form-control" v-model="editingApp.name" placeholder="Назва...">
                            </div>
                            <div class="col-md-2">
                                <label class="form-label">Іконка</label>
                                <div class="input-group">
                                    <span class="input-group-text bg-dark-lt">{{ editingApp.icon || '📱' }}</span>
                                    <select class="form-select px-2" v-model="editingApp.icon" style="max-width:60px;">
                                        <option v-for="e in ['📱','🏠','💼','🎬','🎨','🚀','🔥','💎','⚡','🛠️','🧩','📦']" :key="e" :value="e">{{e}}</option>
                                    </select>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="text-muted small mb-1">Або введіть свій емодзі:</div>
                                <input type="text" class="form-control" v-model="editingApp.icon" maxlength="4" placeholder="📱">
                            </div>
                        </div>

                        <div class="mb-3">
                            <label class="form-label">Опис додатка</label>
                            <textarea class="form-control" v-model="editingApp.description" rows="2" placeholder="Короткий опис можливостей..."></textarea>
                        </div>

                        <label class="form-label d-flex justify-content-between">
                            <span>Склад додатка (Модулі):</span>
                            <span v-if="publishedCount > 0" class="badge bg-success-lt small">
                                {{ publishedCount }} ШІ-модулів доступно
                            </span>
                        </label>
                        
                        <div class="list-group mb-3 editor-modules-list">
                            <!-- Selected modules first (sortable) -->
                            <div v-for="mod in modulesListForEditor" :key="mod.id" 
                                class="list-group-item bg-dark-lt border-0 d-flex align-items-center gap-3 p-2 mb-1 rounded"
                                :class="{'selected-module border-start border-primary border-4': editingApp.modules.includes(mod.id), 'opacity-50': !editingApp.modules.includes(mod.id)}">
                                <input class="form-check-input m-0" type="checkbox" :value="mod.id" v-model="editingApp.modules">
                                <div class="flex-grow-1 ps-2">
                                    <div class="d-flex align-items-center gap-2">
                                        <span>{{ mod.icon }}</span>
                                        <span class="fw-bold">{{ mod.label }}</span>
                                    </div>
                                    <div class="text-muted" style="font-size:0.7rem;">{{ mod.desc || mod.id }}</div>
                                </div>
                                <div v-if="editingApp.modules.includes(mod.id)" class="d-flex gap-1">
                                    <button class="btn btn-sm btn-ghost-primary btn-icon" @click.stop="moveModule(mod.id, -1)" 
                                        :disabled="editingApp.modules.indexOf(mod.id) === 0">↑</button>
                                    <button class="btn btn-sm btn-ghost-primary btn-icon" @click.stop="moveModule(mod.id, 1)" 
                                        :disabled="editingApp.modules.indexOf(mod.id) === editingApp.modules.length - 1">↓</button>
                                </div>
                            </div>
                        </div>
                        <div class="d-flex gap-2">
                            <button class="btn btn-primary" @click="saveCustomApp">Зберегти</button>
                            <button class="btn btn-ghost-secondary" @click="editingApp = null">Скасувати</button>
                        </div>
                    </div>

                    <div class="row g-3">
                        <div class="col-md-6" v-for="app in localCustomApps" :key="app.id">
                            <div class="card shadow-sm border-0 h-100">
                                <div class="card-body p-3 d-flex align-items-start gap-3">
                                    <div class="avatar avatar-md bg-purple-lt" style="font-size: 1.5rem;">{{ app.icon || '📱' }}</div>
                                    <div class="flex-grow-1">
                                        <div class="fw-bold d-flex align-items-center gap-2 text-white">
                                            {{ app.name }}
                                            <span v-if="localSettings.dock_apps.includes('custom_app_' + app.id)" class="badge bg-info-lt">В Dock</span>
                                        </div>
                                        <div class="text-muted small">{{ app.description }}</div>
                                        <div class="text-muted" style="font-size:0.7rem; margin-top:4px;">
                                            Склад: 
                                            <span v-for="m in app.modules" :key="m" class="badge bg-dark-lt text-muted me-1">{{ getModuleLabel(m) }}</span>
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
                        <div v-if="!localCustomApps.length && !editingApp" class="col-12 py-4 text-center text-muted border border-dashed rounded">
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
    props: ['user', 'systemSettings', 'auth', 'navItems', 'customAppsProp'],
    data() {
        return {
            settingsTab: 'profile',
            loading: false,
            saveSuccess: false,
            newSocial: { name: '', link: '' },
            localSettings: { dock_apps: [], ...this.systemSettings },
            copySuccess: false,
            localCustomApps: [...(this.customAppsProp || [])],
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
                { id: 'profile', label: 'Профіль', icon: '👤', comp: 'eme-profile', desc: 'Управління персональними даними та аватаром' },
                { id: 'network', label: 'Мережа (Mesh)', icon: '🌐', comp: 'eme-network', desc: 'Зв’язок між нодами, децентралізований шеринг' },
                { id: 'chat', label: 'Чат', icon: '💬', comp: 'eme-chat', desc: 'Приватні та групові повідомлення' },
                { id: 'gallery', label: 'Галерея', icon: '🖼️', comp: 'eme-gallery', desc: 'Перегляд та менеджмент медіафайлів' },
                { id: 'indexer', label: 'Індексатор', icon: '📤', comp: 'eme-indexer', desc: 'Завантаження та обробка локальних файлів' },
                { id: 'projects', label: 'Проєкти', icon: '📁', comp: 'eme-projects', desc: 'Система керування знаннями та кодом' },
                { id: 'tasks', label: 'Завдання', icon: '✅', comp: 'eme-vikunja', desc: 'To-do списки, інтегровані з Vikunja' },
                { id: 'memos', label: 'Нотатки', icon: '📝', comp: 'eme-memos', desc: 'Думки та короткі записи (аналог Twitter/Threads)' },
                { id: 'bookmarks', label: 'Закладки', icon: '🔖', comp: 'eme-bookmarks', desc: 'Збережені посилання та ресурси' },
                { id: 'mafia', label: 'ШІ Мафія', icon: '🎭', comp: 'eme-mafia', desc: 'Інтерактивна гра з ШІ-агентами' },
                { id: 'omnitools', label: 'OmniTools', icon: '🧰', comp: 'eme-omni-tools', desc: 'Набір корисних утиліт та інструментів ШІ' },
                { id: 'feed', label: 'Стіна', icon: '📰', comp: 'eme-feed', desc: 'Глобальна стрічка подій mesh-мережі' },
                { id: 'aibuilder', label: 'AI App Builder', icon: '🤖', comp: 'eme-a-i-builder', desc: 'Генерація нових Vue-компонентів за допомогою LLM' },
            ];
            
            
            // MERGE ALL SOURCES
            const fromProp = (this.systemSettings && this.systemSettings.published_modules) ? this.systemSettings.published_modules : [];
            const fromFetch = this.fetchedPublishedModules || [];
            
            // Deduplicate by ID
            const uniqueMap = new Map();
            fromProp.forEach(m => { if(m && m.id) uniqueMap.set(m.id, m); });
            fromFetch.forEach(m => { if(m && m.id) uniqueMap.set(m.id, m); });
            const uniquePublished = Array.from(uniqueMap.values());
            
            console.log("EME Builder Debug: Base=13, Published=", uniquePublished.length, uniquePublished);
            
            return [...baseModules, ...uniquePublished];
        },
        modulesListForEditor() {
            if (!this.editingApp) return this.availableModulesForBuilder;
            const selectedIds = this.editingApp.modules || [];
            const all = this.availableModulesForBuilder;
            
            // Selected modules in their custom order
            const selected = selectedIds.map(id => all.find(m => m.id === id)).filter(Boolean);
            // Unselected modules remaining
            const unselected = all.filter(m => !selectedIds.includes(m.id));
            
            return [...selected, ...unselected];
        },
        publishedCount() {
            const m = this.availableModulesForBuilder;
            return m.filter(x => !['profile','network','chat','gallery','indexer','projects','tasks','memos','bookmarks','mafia','omnitools','feed','aibuilder'].includes(x.id)).length;
        },
        navItemsAvailable() {
            const core = [
                { item_id: 'apps_store', label: 'Маркет', icon: '🛍️', description: 'Встановлення нових модулів та сервісів' },
                { item_id: 'settings', label: 'Налашт.', icon: '⚙️', description: 'Профіль, теми та системні опції' }
            ];
            
            const custom = (this.localCustomApps || []).map(app => ({
                item_id: 'custom_app_' + app.id,
                label: app.name,
                icon: app.icon || '📱',
                description: app.description || 'Власний додаток',
                isCustom: true
            }));
            
            return [...core, ...custom];
        },
        sortedDockItems() {
            const all = this.navItemsAvailable;
            const dock = this.localSettings.dock_apps || [];
            
            // Items in dock according to their order
            const inDock = dock.map(id => all.find(x => x.item_id === id)).filter(Boolean);
            // Items NOT in dock
            const notInDock = all.filter(x => !dock.includes(x.item_id));
            
            return [...inDock, ...notInDock];
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
        this.fetchCustomApps();
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
        async fetchCustomApps() {
            try {
                const res = await fetch('/api/settings/apps/', { headers: this.auth() });
                const data = await res.json();
                let results = data.results || data;
                results.sort((a, b) => (a.order || 0) - (b.order || 0));
                this.localCustomApps = results;
                this.$emit('update:custom-apps', results);
            } catch (e) { }
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
                let results = data.results || data;
                // Sort by order
                results.sort((a, b) => (a.order || 0) - (b.order || 0));
                this.customApps = results;
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
        moveDockItem(itemId, direction) {
            const dock = [...(this.localSettings.dock_apps || [])];
            const idx = dock.indexOf(itemId);
            if (idx === -1) return;
            
            const newIndex = idx + direction;
            if (newIndex < 0 || newIndex >= dock.length) return;
            
            const temp = dock[idx];
            dock[idx] = dock[newIndex];
            dock[newIndex] = temp;
            
            this.localSettings.dock_apps = dock;
        },
        async updateAppOrder(app) {
            try {
                await fetch(`/api/settings/apps/${app.id}/`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json', ...this.auth() },
                    body: JSON.stringify({ order: app.order })
                });
            } catch (e) {}
        },
        moveModule(modId, direction) {
            const idx = this.editingApp.modules.indexOf(modId);
            if (idx === -1) return;
            
            const newIndex = idx + direction;
            if (newIndex < 0 || newIndex >= this.editingApp.modules.length) return;
            
            const mods = [...this.editingApp.modules];
            const temp = mods[idx];
            mods[idx] = mods[newIndex];
            mods[newIndex] = temp;
            
            this.editingApp.modules = [...mods];
        },
        getModuleLabel(modId) {
            const m = this.availableModulesForBuilder.find(x => x.id === modId);
            return m ? m.label : modId;
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
    background: var(--eme-grad);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
}
</style>
