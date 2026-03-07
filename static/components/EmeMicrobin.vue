<template>
    <div class="eme-scroll-container">
        <div class="container-fluid py-4 min-vh-100">
            <header class="mb-4">
                <div class="d-flex align-items-center gap-3">
                    <div class="header-icon-box">📋</div>
                    <div>
                        <h1 class="page-title m-0">EME Pastebin</h1>
                        <p class="text-muted m-0">Швидкий та безпечний обмін текстом і кодом</p>
                    </div>
                </div>
            </header>

            <div class="row g-4">
                <!-- Sidebar: History -->
                <div class="col-md-3">
                    <div class="card bg-dark border-secondary h-100">
                        <div class="card-header border-secondary d-flex justify-content-between align-items-center">
                            <h3 class="card-title text-white m-0">Мої Сніпети</h3>
                            <button class="btn btn-sm btn-primary" @click="createNew">+ Новий</button>
                        </div>
                        <div class="list-group list-group-flush list-group-transparent p-2">
                            <a href="#" class="list-group-item list-group-item-action text-white" 
                               v-for="snip in mySnippets" :key="snip.id"
                               @click.prevent="openSnippet(snip.short_code)"
                               :class="{ active: currentSnippet && currentSnippet.id === snip.id }">
                                <span class="d-block text-truncate fw-bold">{{ snip.title || 'Безіменний' }}</span>
                                <small class="text-muted">Код: {{ snip.short_code }}</small>
                            </a>
                            <div v-if="mySnippets.length === 0" class="text-muted p-3 text-center">
                                Історія порожня.
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Main Area -->
                <div class="col-md-9">
                    <div class="card bg-dark border-secondary p-4 h-100">
                        <!-- CREATE NEW / EDIT MODE -->
                        <div v-if="mode === 'create'">
                            <div class="d-flex gap-2 mb-3">
                                <input type="text" v-model="form.title" class="form-control bg-dark text-white border-secondary" placeholder="Коротка назва (опціонально)">
                                <select v-model="form.syntax" class="form-select bg-dark text-white border-secondary" style="width: auto;">
                                    <option value="plaintext">Text</option>
                                    <option value="python">Python</option>
                                    <option value="javascript">JavaScript</option>
                                    <option value="json">JSON</option>
                                </select>
                            </div>
                            
                            <textarea v-model="form.content" class="form-control bg-black text-white border-secondary mb-3" rows="15" placeholder="Вставте текст сюди..." style="font-family: monospace;"></textarea>
                            
                            <div class="d-flex justify-content-between align-items-center">
                                <div class="form-check form-switch cursor-pointer">
                                    <input class="form-check-input" type="checkbox" v-model="form.is_public" id="publicSwitch">
                                    <label class="form-check-label text-white" for="publicSwitch">Публічний доступ</label>
                                </div>
                                <button class="btn btn-primary" :disabled="!form.content.trim() || isSubmitting" @click="saveSnippet">
                                    <span v-if="!isSubmitting">💾 Зберегти Сніпет</span>
                                    <span v-else>Завантаження...</span>
                                </button>
                            </div>
                        </div>

                        <!-- VIEW MODE -->
                        <div v-else-if="mode === 'view' && currentSnippet">
                            <div class="d-flex justify-content-between align-items-start mb-3">
                                <div>
                                    <h2 class="text-white mb-1">{{ currentSnippet.title || 'Безіменний Сніпет' }}</h2>
                                    <span class="badge bg-secondary">Формат: {{ currentSnippet.syntax }}</span>
                                    <span class="badge" :class="currentSnippet.is_public ? 'bg-success' : 'bg-danger'" class="ms-2">
                                        {{ currentSnippet.is_public ? 'Публічний' : 'Приватний' }}
                                    </span>
                                </div>
                                <div class="d-flex gap-2">
                                    <button class="btn btn-outline-info" @click="copyLink">🔗 Копіювати посилання</button>
                                    <button class="btn btn-outline-light" @click="copyContent">📋 Скопіювати текст</button>
                                </div>
                            </div>

                            <div class="alert alert-info py-2 mb-3 d-flex justify-content-between align-items-center">
                                <span>Короткиий код: <strong>{{ currentSnippet.short_code }}</strong></span>
                                <small>Створено: {{ new Date(currentSnippet.created_at).toLocaleString('uk-UA') }}</small>
                            </div>

                            <pre class="bg-black text-white border border-secondary p-3 rounded" style="overflow-x: auto;">{{ currentSnippet.content }}</pre>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    props: ['user', 'auth'],
    data() {
        return {
            mode: 'create', // 'create' or 'view'
            mySnippets: [],
            currentSnippet: null,
            form: {
                title: '',
                content: '',
                syntax: 'plaintext',
                is_public: true
            },
            isSubmitting: false
        }
    },
    methods: {
        async fetchMySnippets() {
            try {
                const res = await fetch('/api/utils/pastebin/', { headers: this.auth() });
                if(res.ok) {
                    const data = await res.json();
                    this.mySnippets = data.results || data;
                }
            } catch(e) { console.error('Error fetching snippets', e); }
        },
        createNew() {
            this.currentSnippet = null;
            this.mode = 'create';
            this.form = { title: '', content: '', syntax: 'plaintext', is_public: true };
        },
        async saveSnippet() {
            this.isSubmitting = true;
            try {
                const res = await fetch('/api/utils/pastebin/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', ...this.auth() },
                    body: JSON.stringify(this.form)
                });
                
                if (res.ok) {
                    const data = await res.json();
                    this.currentSnippet = data;
                    this.mode = 'view';
                    this.fetchMySnippets(); // Refresh sidebar list
                } else {
                    alert('Помилка збереження');
                }
            } catch(e) {
                alert('Мережева помилка');
            } finally {
                this.isSubmitting = false;
            }
        },
        async openSnippet(code) {
            try {
                const res = await fetch(`/api/utils/pastebin/by_code/${code}/`, { headers: this.auth() });
                if(res.ok) {
                    this.currentSnippet = await res.json();
                    this.mode = 'view';
                } else {
                    alert('Сніпет не знайдено або доступ заборонено.');
                }
            } catch(e) { console.error(e); }
        },
        copyLink() {
            // EME OS approach: link format can be #/snippet/XYZ or we just copy the code
            const url = window.location.origin + window.location.pathname + '#!/microbin/' + this.currentSnippet.short_code;
            navigator.clipboard.writeText(url);
            alert('Посилання скопійовано! (В наступних фазах ми додамо обробку URL хешів)');
        },
        copyContent() {
            navigator.clipboard.writeText(this.currentSnippet.content);
            alert('Текст скопійовано!');
        }
    },
    mounted() {
        this.fetchMySnippets();
    }
}
</script>

<style scoped>
.page-title {
    font-size: 1.8rem;
    font-weight: 800;
    color: white;
}

.header-icon-box {
    width: 50px;
    height: 50px;
    background: var(--eme-grad);
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.8rem;
    box-shadow: 0 4px 15px rgba(0, 229, 255, 0.3);
}

.list-group-item.active {
    background: rgba(0, 229, 255, 0.1) !important;
    border-color: rgba(0, 229, 255, 0.3) !important;
}
</style>
