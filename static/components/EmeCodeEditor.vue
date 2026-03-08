<template>
    <div class="eme-code-editor-overlay" v-if="isOpen" :class="{ 'minimized': isMinimized }">
        <div class="eme-editor-window card shadow-lg">
            <!-- Window Header -->
            <div class="card-header bg-dark text-white d-flex justify-content-between align-items-center p-2 drag-handle">
                <div class="d-flex align-items-center gap-2">
                    <span style="font-size: 1.2rem;">📝</span>
                    <strong class="text-white">{{ draftName || 'Редактор коду' }}</strong>
                    <span v-if="isUnsaved" class="badge bg-warning ms-2">незбережено</span>
                </div>
                <div class="d-flex gap-2">
                    <button class="btn btn-sm btn-ghost-light p-1" @click="isMinimized = !isMinimized">
                        <span v-if="isMinimized">🗗</span>
                        <span v-else>🗕</span>
                    </button>
                    <button class="btn btn-sm btn-ghost-danger p-1" @click="closeEditor">✕</button>
                </div>
            </div>

            <!-- Editor Body -->
            <div class="card-body p-0 d-flex flex-column overflow-hidden" v-show="!isMinimized">
                <!-- Tabs Header -->
                <div class="bg-dark px-2 pt-2 border-bottom">
                    <ul class="nav nav-tabs border-0" style="gap: 5px;">
                        <li class="nav-item">
                            <button class="nav-link py-1 px-3 border-0 rounded-top text-white" 
                                :class="{ 'active bg-light text-dark': activeTab === 'code' }"
                                @click="activeTab = 'code'">
                                💻 Code
                            </button>
                        </li>
                        <li class="nav-item">
                            <button class="nav-link py-1 px-3 border-0 rounded-top text-white" 
                                :class="{ 'active bg-light text-dark': activeTab === 'agent' }"
                                @click="activeTab = 'agent'">
                                🧠 AI Agent
                            </button>
                        </li>
                    </ul>
                </div>

                <!-- Toolbar -->
                <div class="editor-toolbar d-flex gap-2 p-2 border-bottom bg-light">
                    <button class="btn btn-sm btn-primary d-flex align-items-center gap-1" @click="save" :disabled="isSaving">
                        <span v-if="isSaving" class="spinner-border spinner-border-sm"></span>
                        <span v-else>💾</span> Зберегти {{ activeTab === 'code' ? 'Код' : 'Налаштування' }}
                    </button>
                    <button class="btn btn-sm btn-outline-info d-flex align-items-center gap-1" @click="preview">
                        <span>👁️</span> Preview
                    </button>
                    <button class="btn btn-sm btn-outline-success d-flex align-items-center gap-1 ms-auto" @click="pushToGit">
                        <span>📤</span> Push to Git
                    </button>
                </div>

                <!-- Main Content Areas -->
                <div class="flex-grow-1 position-relative overflow-auto" style="height: 60vh;">
                    <!-- CODE TAB -->
                    <div v-show="activeTab === 'code'" class="h-100">
                        <textarea 
                            class="form-control h-100 border-0 font-monospace bg-dark text-light p-3" 
                            style="resize: none; font-size: 13px; line-height: 1.5;" 
                            v-model="code"
                            @input="isUnsaved = true"
                            spellcheck="false"
                        ></textarea>
                    </div>

                    <!-- AGENT TAB -->
                    <div v-show="activeTab === 'agent'" class="p-3 bg-dark text-white">
                        <div class="mb-3">
                            <label class="form-label text-white">System Prompt (Context for this app's AI)</label>
                            <textarea class="form-control bg-dark border-secondary text-white" rows="6" 
                                v-model="agentPrompt" @input="isUnsaved = true"
                                placeholder="Наприклад: 'Ти експерт з бухгалтерії. Допомагай користувачу рахувати податки...'"></textarea>
                        </div>
                        <div class="mb-3">
                            <label class="form-label text-white">Доступні скіли (JSON Array of skill IDs)</label>
                            <input type="text" class="form-control bg-dark border-secondary text-white" 
                                v-model="skillsRaw" @input="validateSkills"
                                placeholder='["knowledge_base", "web_search", "calculator"]'>
                            <div v-if="skillsError" class="text-danger small mt-1">{{ skillsError }}</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Minimized Tab (only shown if minimized) -->
            <div v-if="isMinimized" class="p-2 text-center text-muted" style="cursor: pointer;" @click="isMinimized = false">
                Натисніть щоб розгорнути
            </div>
        </div>
    </div>
</template>

<script>
export default {
    props: ['auth', 'draftId'],
    data() {
        return {
            isOpen: true,
            isMinimized: false,
            isSaving: false,
            isUnsaved: false,
            activeTab: 'code',
            code: '',
            agentPrompt: '',
            skillsRaw: '[]',
            skillsError: '',
            draftName: '',
            componentName: ''
        }
    },
    watch: {
        draftId: {
            immediate: true,
            handler(newVal) {
                if (newVal) this.loadDraft(newVal);
            }
        }
    },
    methods: {
        validateSkills() {
            try {
                const parsed = JSON.parse(this.skillsRaw);
                if (!Array.isArray(parsed)) throw new Error("Мусить бути масивом");
                this.skillsError = '';
                this.isUnsaved = true;
            } catch (e) {
                this.skillsError = "Невалідний формат JSON масиву";
            }
        },
        async loadDraft(id) {
            try {
                const res = await fetch(`/api/settings/ai-drafts/${id}/`, { headers: this.auth() });
                if (res.ok) {
                    const data = await res.json();
                    this.code = data.vue_code;
                    this.agentPrompt = data.agent_prompt || '';
                    this.skillsRaw = JSON.stringify(data.skills || []);
                    this.draftName = data.name;
                    this.componentName = data.component_name;
                    this.isUnsaved = false;
                }
            } catch (e) {
                console.error("Load error", e);
            }
        },
        async save() {
            if (!this.draftId || this.skillsError) return;
            this.isSaving = true;
            try {
                const res = await fetch(`/api/settings/ai-drafts/${this.draftId}/`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json', ...this.auth() },
                    body: JSON.stringify({ 
                        vue_code: this.code,
                        agent_prompt: this.agentPrompt,
                        skills: JSON.parse(this.skillsRaw)
                    })
                });
                if (res.ok) {
                    this.isUnsaved = false;
                }
            } catch (e) {
                alert("Помилка збереження.");
            }
            this.isSaving = false;
        },
        async preview() {
            if (!this.code) return;
            try {
                const res = await fetch('/api/settings/ai-builder/preview/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', ...this.auth() },
                    body: JSON.stringify({ code: this.code, name: this.componentName })
                });
                if (res.ok) {
                    // Tell root to open the preview component
                    this.$root.activeApp = 'eme-preview';
                    // Optional: minimize editor or stay open
                    this.isMinimized = true;
                }
            } catch (e) {
                alert("Помилка при підготовці Preview.");
            }
        },
        async pushToGit() {
            if (!this.draftId) return;
            if (this.isUnsaved) {
                if (!confirm("У вас є незбережені зміни. Зберегти і відправити в Git?")) return;
                await this.save();
            }
            this.isSaving = true;
            try {
                const res = await fetch(`/api/settings/ai-builder/push/${this.draftId}/`, {
                    method: 'POST',
                    headers: this.auth()
                });
                const data = await res.json();
                if (res.ok) {
                    alert("Успіх! " + data.message);
                } else {
                    alert("Помилка Git: " + data.error);
                }
            } catch (e) {
                alert("Помилка підключення до сервера.");
            }
            this.isSaving = false;
        },
        closeEditor() {
            if (this.isUnsaved) {
                if (!confirm("У вас є незбережені зміни. Закрити редактор?")) return;
            }
            this.$root.isEditorOpen = false;
        }
    }
}
</script>

<style scoped>
.eme-code-editor-overlay {
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 600px;
    max-width: 90vw;
    z-index: 9999;
}

.eme-editor-window {
    border: 2px solid var(--eme-accent);
    background: #1a1c2e;
    border-radius: 12px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
}

.eme-code-editor-overlay.minimized {
    width: 250px;
}

.eme-code-editor-overlay.minimized .eme-editor-window {
    border-width: 1px;
}

.drag-handle {
    cursor: default; /* For future draggable implementation */
}

.btn-ghost-light {
    color: white;
    opacity: 0.7;
}
.btn-ghost-light:hover {
    opacity: 1;
    background: rgba(255,255,255,0.1);
}

textarea:focus {
    box-shadow: none;
    outline: none;
}
</style>
