<template>
    <div class="clone-shell">

        <div class="clone-header">
            <div class="d-flex align-items-center gap-3">
                <span class="clone-title">📦 Клон Мастер</span>
                <span class="badge bg-cyan-lt">v2.0</span>
            </div>
            <div class="d-flex gap-2 align-items-center">
                <span class="text-muted small" v-if="serverIp">🌐 {{ serverIp }}</span>
                <button class="btn btn-sm btn-ghost-secondary" @click="$emit('close')">✕</button>
            </div>
        </div>

        <div class="d-flex flex-grow-1 overflow-hidden">

            <!-- LEFT: Module Selector -->
            <div class="clone-sidebar overflow-auto">
                <div class="px-4 pt-3 pb-2 d-flex justify-content-between align-items-center">
                    <div class="small fw-bold text-muted" style="letter-spacing:1px;">МОДУЛІ</div>
                    <button class="btn btn-xs btn-ghost-primary" @click="selectAllModules" style="font-size: 10px;">
                        {{ selectedModules.length === modules.length && modules.length > 0 ? 'Зняти всі' : 'Вибрати всі' }}
                    </button>
                </div>

                <div v-for="mod in modules" :key="mod.id"
                    class="mod-item"
                    :class="{ active: isSelected(mod.id), 'mod-system': mod.is_system }"
                    @click="toggleModule(mod.id)">
                    <div class="mod-check">
                        <div class="check-box" :class="{ checked: isSelected(mod.id) }">
                            <span v-if="isSelected(mod.id)">✓</span>
                        </div>
                    </div>
                    <div>
                        <div class="d-flex align-items-center gap-2">
                            <span>{{ mod.icon }} {{ mod.name }}</span>
                            <span v-if="mod.is_system" class="badge bg-blue-lt" style="font-size:9px;">Core</span>
                        </div>
                        <div class="mod-desc">{{ mod.desc }}</div>
                        <div class="mod-deps" v-if="mod.deps.length">Deps: {{ mod.deps.join(', ') }}</div>
                    </div>
                </div>
            </div>

            <!-- RIGHT: Options + Result -->
            <div class="flex-grow-1 overflow-auto p-4">

                <!-- Clone Name -->
                <div class="option-card mb-3">
                    <div class="option-card-title mb-3">🏷️ Назва клону</div>
                    <input class="form-control" v-model="cloneName" placeholder="my_eme_clone">
                </div>

                <!-- Options -->
                <div class="option-card mb-3">
                    <div class="option-card-title mb-3">⚙️ Параметри</div>

                    <div class="option-row">
                        <div>
                            <div class="fw-bold">🗄️ База даних</div>
                            <div class="small text-muted">Включити db.sqlite3 з усіма даними</div>
                        </div>
                        <div class="form-check form-switch">
                            <input class="form-check-input" type="checkbox" v-model="includeDb">
                        </div>
                    </div>

                    <div class="option-row">
                        <div>
                            <div class="fw-bold">🖼️ Медіа-файли</div>
                            <div class="small text-muted">Включити папку media/ (фото, документи)</div>
                        </div>
                        <div class="form-check form-switch">
                            <input class="form-check-input" type="checkbox" v-model="includeMedia">
                        </div>
                    </div>

                    <div class="option-row">
                        <div>
                            <div class="fw-bold">🌱 Seed-скрипти</div>
                            <div class="small text-muted">Авто-наповнення даних після міграцій</div>
                        </div>
                        <div class="form-check form-switch">
                            <input class="form-check-input" type="checkbox" v-model="includeSeeds">
                        </div>
                    </div>
                </div>

                <!-- Summary -->
                <div class="option-card mb-4">
                    <div class="option-card-title mb-3">📊 Підсумок</div>
                    <div class="d-flex flex-wrap gap-2">
                        <div class="summary-pill" v-for="m in selectedModules" :key="m">{{ m }}</div>
                        <div v-if="!selectedModules.length" class="text-muted small">Нічого не обрано</div>
                    </div>
                    <div class="small text-muted mt-2">+ Core: eme, profiles, system_settings, eme_nav (авто)</div>
                </div>

                <!-- Quick Full Backup Button -->
                <button v-if="selectedModules.length < modules.length || !includeDb || !includeMedia" class="btn btn-outline-info w-100 mb-2"
                    @click="setupFullBackup"
                    style="padding: 0.5rem; font-size: 0.9rem;">
                    🚀 Підготувати повний бекап всього сайту
                </button>

                <!-- Create Button -->
                <button class="btn btn-primary w-100 mb-3"
                    :disabled="loading || !selectedModules.length"
                    @click="createClone"
                    style="padding: 0.75rem; font-size: 1rem;">
                    <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
                    {{ loading ? 'Пакування...' : '📦 Згенерувати Клон' }}
                </button>

                <!-- Result Card -->
                <transition name="fade">
                    <div v-if="showResult" class="result-card p-4">
                        <div class="d-flex align-items-center gap-3 mb-4">
                            <span style="font-size: 3rem;">✅</span>
                            <div>
                                <div class="fw-bold fs-4">Клон готовий!</div>
                                <div class="text-muted small">{{ resultFilename }} · {{ resultSizeKb }} KB</div>
                            </div>
                        </div>

                        <!-- QR Code -->
                        <div class="text-center mb-4">
                            <div class="d-inline-block p-2 rounded" style="background:white;">
                                <img :src="qrUrl" alt="QR" style="width:180px;height:180px;">
                            </div>
                            <div class="small text-muted mt-2">Відскануйте QR в Termux на телефоні</div>
                        </div>

                        <!-- Termux Command -->
                        <div class="mb-3">
                            <div class="small text-muted mb-1">📱 Команда для Termux:</div>
                            <div class="code-block d-flex align-items-start gap-2">
                                <code class="flex-grow-1" style="white-space: pre-wrap; word-break: break-all; font-size: .75rem;">{{ termuxCommand }}</code>
                                <button class="btn btn-xs btn-ghost-secondary flex-shrink-0" @click="copy(termuxCommand, 'cmd')">{{ copied === 'cmd' ? '✓' : '📋' }}</button>
                            </div>
                        </div>

                        <!-- Direct Link -->
                        <div class="mb-3">
                            <div class="small text-muted mb-1">🔗 Пряме посилання:</div>
                            <div class="code-block d-flex align-items-center gap-2">
                                <code class="flex-grow-1" style="font-size: .75rem;">{{ absoluteUrl }}</code>
                                <button class="btn btn-xs btn-ghost-secondary" @click="copy(absoluteUrl, 'link')">{{ copied === 'link' ? '✓' : '📋' }}</button>
                            </div>
                        </div>

                        <!-- Setup Instructions -->
                        <div class="mt-3 p-3 rounded" style="background: rgba(0,229,255,0.05); border: 1px solid rgba(0,229,255,0.1);">
                            <div class="fw-bold mb-2 small">📋 Інструкція встановлення</div>
                            <ol class="small text-muted mb-0 ps-3">
                                <li>Відкрийте <strong>Termux</strong> на телефоні.</li>
                                <li>Відскануйте QR або вставте команду.</li>
                                <li>Система сама завантажить, розпакує та запустить EME.</li>
                                <li>Відкрийте браузер: <code>http://localhost:8000</code></li>
                            </ol>
                        </div>
                    </div>
                </transition>

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
            selectedModules: ['projects', 'network', 'eme_media', 'clone_master'],
            includeDb: false,
            includeMedia: false,
            includeSeeds: true,
            cloneName: '',
            loading: false,
            showResult: false,
            resultUrl: '',
            resultFilename: '',
            resultSizeKb: 0,
            resultModulesCount: 0,
            serverIp: '',
            copied: null,
        };
    },
    computed: {
        absoluteUrl() {
            if (!this.resultUrl) return '';
            const base = this.serverIp ? `http://${this.serverIp}:8000` : window.location.origin;
            return base + this.resultUrl;
        },
        termuxCommand() {
            if (!this.absoluteUrl) return '';
            const dir = this.cloneName || 'eme';
            return `pkg install -y python curl unzip git && mkdir -p ${dir} && cd ${dir} && curl -L "${this.absoluteUrl}" -o clone.zip && unzip -o clone.zip && rm clone.zip && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && python manage.py migrate && bash start.sh`;
        },
        qrUrl() {
            if (!this.termuxCommand) return '';
            return `https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${encodeURIComponent(this.termuxCommand)}`;
        },
    },
    methods: {
        hdrs() {
            const token = localStorage.getItem('access_token');
            return { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token };
        },
        isSelected(id) {
            return this.selectedModules.includes(id);
        },
        toggleModule(id) {
            const idx = this.selectedModules.indexOf(id);
            if (idx === -1) {
                this.selectedModules.push(id);
                // Auto-add deps
                const mod = this.modules.find(m => m.id === id);
                if (mod?.deps) {
                    mod.deps.forEach(dep => {
                        if (!this.selectedModules.includes(dep)) this.selectedModules.push(dep);
                    });
                }
            } else {
                this.selectedModules.splice(idx, 1);
            }
        },
        selectAllModules() {
            if (this.selectedModules.length === this.modules.length && this.modules.length > 0) {
                // Deselect all non-system
                this.selectedModules = this.modules.filter(m => m.is_system).map(m => m.id);
            } else {
                this.selectedModules = this.modules.map(m => m.id);
            }
        },
        setupFullBackup() {
            this.selectedModules = this.modules.map(m => m.id);
            this.includeDb = true;
            this.includeMedia = true;
            this.includeSeeds = true;
            this.cloneName = 'eme_full_backup';
        },
        async fetchModules() {
            try {
                const res = await fetch('/api/clone/modules/', { headers: this.hdrs() });
                if (res.ok) this.modules = await res.json();
            } catch (e) {}
        },
        async fetchIp() {
            try {
                const res = await fetch('/api/clone/ip/', { headers: this.hdrs() });
                if (res.ok) this.serverIp = (await res.json()).ip;
            } catch (e) {}
        },
        async createClone() {
            this.loading = true;
            this.showResult = false;
            try {
                const res = await fetch('/api/clone/create/', {
                    method: 'POST', headers: this.hdrs(),
                    body: JSON.stringify({
                        modules: this.selectedModules,
                        include_db: this.includeDb,
                        include_media: this.includeMedia,
                        include_seeds: this.includeSeeds,
                        clone_name: this.cloneName || undefined,
                    })
                });
                if (res.ok) {
                    const data = await res.json();
                    this.resultUrl = data.url;
                    this.resultFilename = data.filename;
                    this.resultSizeKb = data.size_kb;
                    this.resultModulesCount = data.modules_count;
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
        copy(text, key) {
            navigator.clipboard.writeText(text);
            this.copied = key;
            setTimeout(() => this.copied = null, 2000);
        },
    },
    mounted() {
        this.fetchModules();
        this.fetchIp();
    }
};
</script>

<style scoped>
.clone-shell {
    background: #0d0f1a;
    color: #e2e8f0;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

.clone-header {
    background: rgba(26, 28, 46, 0.8);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid rgba(255,255,255,0.05);
    padding: 1.25rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: sticky;
    top: 0;
    z-index: 10;
}

.clone-title {
    font-size: 1.4rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    background: var(--eme-grad);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
}

.clone-sidebar {
    width: 300px;
    flex-shrink: 0;
    background: rgba(18, 20, 34, 0.6);
    border-right: 1px solid rgba(255,255,255,0.05);
    backdrop-filter: blur(8px);
}

/* MODULE ITEMS */
.mod-item {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 10px 16px;
    cursor: pointer;
    transition: background .15s;
    border-left: 3px solid transparent;
}
.mod-item:hover { background: rgba(255,255,255,0.04); }
.mod-item.active {
    background: rgba(0,229,255,0.07);
    border-left-color: #00e5ff;
}
.mod-item.mod-system { opacity: 0.7; pointer-events: none; border-left-color: rgba(59,130,246,0.4); }

.check-box {
    width: 18px; height: 18px;
    border: 2px solid rgba(255,255,255,0.2);
    border-radius: 5px;
    display: flex; align-items: center; justify-content: center;
    font-size: .7rem;
    flex-shrink: 0;
    margin-top: 3px;
    transition: all .15s;
}
.check-box.checked {
    background: #00e5ff;
    border-color: #00e5ff;
    color: #0d0f1a;
    font-weight: 900;
}

.mod-desc { font-size: .75rem; color: #64748b; margin-top: 2px; }
.mod-deps { font-size: .7rem; color: #3b82f6; margin-top: 2px; }
.mod-check { padding-top: 2px; }

/* OPTION CARDS */
.option-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    padding: 1.25rem;
}
.option-card-title {
    font-weight: 700;
    font-size: .9rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-size: .78rem;
}
.option-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: .75rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.04);
}
.option-row:last-child { border-bottom: none; }

/* SUMMARY PILLS */
.summary-pill {
    background: rgba(0,229,255,0.1);
    border: 1px solid rgba(0,229,255,0.15);
    border-radius: 20px;
    padding: 2px 10px;
    font-size: .78rem;
    color: #00e5ff;
}

/* RESULT */
.result-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(0,229,255,0.12);
    border-radius: 16px;
}
.code-block {
    background: rgba(0,0,0,0.3);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 8px;
    padding: 10px 12px;
    font-family: monospace;
    color: #a5f3fc;
}

/* FORM OVERRIDES */
.form-control {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    color: white;
    border-radius: 10px;
}
.form-control:focus {
    background: rgba(255,255,255,0.08);
    border-color: rgba(0,229,255,0.4);
    box-shadow: 0 0 0 3px rgba(0,229,255,0.08);
    color: white;
}
.form-control::placeholder { color: #4a5568; }
.form-check-input:checked { background-color: #00e5ff; border-color: #00e5ff; }

.fade-enter-active, .fade-leave-active { transition: opacity .4s, transform .3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: translateY(12px); }

@media (max-width: 768px) {
    .clone-sidebar { width: 100%; border-right: none; }
}
</style>
