<template>
    <div class="eme-app-page">
        <div class="eme-app-header">
            <div class="d-flex align-items-center gap-2">
                <h1 class="eme-app-title">Клон Мастер</h1>
                <span class="badge bg-purple-lt">v1.0</span>
            </div>
            <button class="btn btn-sm btn-ghost-secondary" @click="$emit('close')">✕</button>
        </div>

        <div class="row g-3">
            <div class="col-md-8">
                <div class="card shadow-sm">
                    <div class="card-header">
                        <h3 class="card-title">Вибір модулів для клонування</h3>
                    </div>
                    <div class="card-body">
                        <p class="text-muted small mb-3">
                            Оберіть частини системи, які ви хочете включити в архів. Базові файли (manage.py, start.sh) додаються автоматично.
                        </p>
                        
                        <div class="list-group list-group-flush mb-4 border rounded">
                            <div v-for="mod in modules" :key="mod.id" class="list-group-item d-flex align-items-center">
                                <label class="form-check form-check-inline mb-0 flex-fill py-1" style="cursor:pointer">
                                    <input class="form-check-input" type="checkbox" v-model="selectedModules" :value="mod.id">
                                    <span class="form-check-label">
                                        <strong>{{ mod.name }}</strong>
                                        <small class="d-block text-muted">/{{ mod.id }}</small>
                                    </span>
                                </label>
                                <span v-if="mod.is_system" class="badge bg-azure-lt ml-auto">Системний</span>
                            </div>
                        </div>

                        <div class="space-y">
                            <label class="form-check form-switch">
                                <input class="form-check-input" type="checkbox" v-model="includeDb">
                                <span class="form-check-label">Включити Базу Даних (db.sqlite3)</span>
                            </label>
                            <label class="form-check form-switch">
                                <input class="form-check-input" type="checkbox" v-model="includeMedia">
                                <span class="form-check-label">Включити Медіа-файли (media/)</span>
                            </label>
                        </div>
                    </div>
                    <div class="card-footer d-flex justify-content-between align-items-center">
                        <div class="text-muted small">
                            Обрано модулів: <strong>{{ selectedModules.length }}</strong>
                        </div>
                        <button class="btn btn-primary" :disabled="loading || !selectedModules.length" @click="createClone">
                            <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
                            {{ loading ? 'Створення...' : 'Згенерувати Клон' }}
                        </button>
                    </div>
                </div>
            </div>

            <div class="col-md-4">
                <div class="card bg-dark-lt">
                    <div class="card-body">
                        <h3 class="card-title mb-2">📜 Кіт Архітектор</h3>
                        <p class="small text-muted">
                            Цей модуль автоматично створює маніфест <code>CLONE_INFO.md</code>, який містить опис структури вашого клону. Це допоможе іншим агентам (або вам) швидше розгорнути систему.
                        </p>
                        <div class="hr-text hr-text-left mt-4">Поради</div>
                        <ul class="small text-muted ps-3">
                            <li>Мінімальний розмір: лише <code>eme</code>.</li>
                            <li>Повний бекап: оберіть все + БД + Медіа.</li>
                            <li>Для Termux: достатньо обрати основні модулі.</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>

        <!-- Result Modal (QR & Link) -->
        <div v-if="showResult" class="modal modal-blur fade show d-block" style="background:rgba(0,0,0,0.5)">
            <div class="modal-dialog modal-md modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-body text-center py-4">
                        <div style="font-size:3.5rem;">📦</div>
                        <h3>Клон готовий до завантаження!</h3>
                        <p class="text-muted">Архів сформовано та збережено на сервері.</p>
                        
                        <div class="my-4 d-flex flex-column align-items-center gap-3">
                            <div class="p-3 bg-white rounded shadow-sm" style="width:240px;height:240px;">
                                <img :src="qrUrl" alt="Clone QR" style="width:100%;height:100%;">
                            </div>
                            
                            <div class="w-100">
                                <label class="form-label small text-start">Команда для Termux (Android):</label>
                                <div class="input-group mb-2">
                                    <input type="text" class="form-control form-control-sm font-monospace bg-dark text-info" readonly :value="termuxCommand">
                                    <button class="btn btn-sm btn-info" @click="copyCommand">
                                        {{ copySuccess ? '👍' : 'Копіювати' }}
                                    </button>
                                </div>
                                <label class="form-label small text-start">Пряме посилання:</label>
                                <div class="input-group">
                                    <input type="text" class="form-control form-control-sm" readonly :value="absoluteUrl">
                                    <button class="btn btn-sm btn-outline-primary" @click="copyLink">
                                        {{ copyLinkSuccess ? '✔' : 'Ланка' }}
                                    </button>
                                </div>
                            </div>
                        </div>

                        <div class="alert alert-info py-2 small text-start">
                            <strong>Інструкція для телефона:</strong>
                            <ol class="mb-0 ps-3">
                                <li>Відкрийте <b>Termux</b>.</li>
                                <li>Вставте скопійовану команду.</li>
                                <li>Система сама завантажить клон, налаштує віртуальне оточення та запустить сервер.</li>
                            </ol>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-primary w-100" @click="showResult=false">Зрозуміло</button>
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
            modules: [],
            selectedModules: ['eme', 'profiles', 'system_settings', 'eme_nav', 'eme_media', 'network'],
            includeDb: false,
            includeMedia: false,
            loading: false,
            showResult: false,
            resultUrl: '',
            resultFilename: '',
            serverIp: '',
            copySuccess: false,
            copyLinkSuccess: false
        }
    },
    mounted() {
        this.fetchModules();
        this.fetchIp();
    },
    methods: {
        async fetchModules() {
            try {
                const res = await fetch('/api/clone/modules/', { headers: this.auth() });
                if (res.ok) {
                    const data = await res.json();
                    this.modules = data.filter(m => !m.is_system);
                }
            } catch (e) { }
        },
        async fetchIp() {
            try {
                const res = await fetch('/api/clone/ip/', { headers: this.auth() });
                if (res.ok) {
                    const data = await res.json();
                    this.serverIp = data.ip;
                }
            } catch (e) { }
        },
        async createClone() {
            this.loading = true;
            try {
                const res = await fetch('/api/clone/create/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', ...this.auth() },
                    body: JSON.stringify({
                        modules: this.selectedModules,
                        include_db: this.includeDb,
                        include_media: this.includeMedia
                    })
                });
                
                if (res.ok) {
                    const data = await res.json();
                    this.resultUrl = data.url;
                    this.resultFilename = data.filename;
                    
                    this.showResult = true;
                } else {
                    alert('Помилка при створенні клону');
                }
            } catch (e) {
                alert('Помилка мережі');
            } finally {
                this.loading = false;
            }
        },
        copyCommand() {
            navigator.clipboard.writeText(this.termuxCommand);
            this.copySuccess = true;
            setTimeout(() => this.copySuccess = false, 2000);
        },
        copyLink() {
            navigator.clipboard.writeText(this.absoluteUrl);
            this.copyLinkSuccess = true;
            setTimeout(() => this.copyLinkSuccess = false, 2000);
        }
    },
    computed: {
        absoluteUrl() {
            if (!this.resultUrl) return '';
            const base = this.serverIp ? `http://${this.serverIp}:8000` : window.location.origin;
            return base + this.resultUrl;
        },
        termuxCommand() {
            if (!this.absoluteUrl) return '';
            const dir = `eme_clone_${Math.floor(Date.now() / 1000)}`;
            return `pkg install -y curl unzip && mkdir -p ${dir} && cd ${dir} && curl -L "${this.absoluteUrl}" -o clone.zip && unzip -o clone.zip && rm clone.zip && bash start.sh`;
        },
        qrUrl() {
            if (!this.termuxCommand) return '';
            // QR standard size for long commands
            return `https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${encodeURIComponent(this.termuxCommand)}`;
        }
    }
}
</script>

<style scoped>
.eme-app-title {
    font-size: 1.4rem;
    font-weight: 800;
    color: var(--tblr-purple);
    margin: 0;
}
</style>
