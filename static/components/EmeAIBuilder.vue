<template>
    <div class="eme-app-page">
        <div class="eme-app-header">
            <div class="d-flex align-items-center gap-3">
                <h1 class="eme-app-title">🤖 AI App Builder</h1>
            </div>
            <button class="btn btn-sm btn-ghost-secondary" @click="$emit('close')">✕</button>
        </div>

        <div class="row g-4">
            <!-- Left Column: Generator & List -->
            <div class="col-md-5 col-lg-4">
                <div class="card mb-4">
                    <div class="card-header bg-primary text-white">
                        <strong class="card-title text-white m-0">💡 Створити новий додаток</strong>
                    </div>
                    <div class="card-body">
                        <div class="mb-3">
                            <label class="form-label">Назва додатку (Eng, CamelCase бажано)</label>
                            <input type="text" class="form-control" v-model="newAppName" placeholder="Наприклад: EmeFeed">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Опис функціоналу</label>
                            <textarea class="form-control" rows="4" v-model="newAppPrompt" 
                                placeholder="Опишіть, що повинен робити цей додаток. AI згенерує Vue компонент."></textarea>
                        </div>
                        <button class="btn btn-primary w-100" @click="generateApp" :disabled="isGenerating || !newAppName || !newAppPrompt">
                            <span v-if="isGenerating" class="spinner-border spinner-border-sm me-2"></span>
                            {{ isGenerating ? 'AI думає...' : 'Згенерувати' }}
                        </button>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h4 class="card-title m-0">📦 Мої розробки (Чернетки)</h4>
                    </div>
                    <div class="list-group list-group-flush" style="max-height: 400px; overflow-y: auto;">
                        <a href="#" v-for="draft in drafts" :key="draft.id" 
                            class="list-group-item list-group-item-action d-flex justify-content-between align-items-center"
                            :class="{ active: selectedDraft && selectedDraft.id === draft.id }"
                            @click.prevent="selectDraft(draft)">
                            <div>
                                <strong>{{ draft.name }}</strong>
                                <div class="small text-muted text-truncate" style="max-width: 180px;">{{ draft.component_name }}</div>
                            </div>
                            <span v-if="draft.is_published" class="badge bg-success">Опубліковано</span>
                            <span v-else class="badge bg-warning">Чернетка</span>
                        </a>
                        <div v-if="!drafts.length" class="p-3 text-center text-muted small">
                            У вас ще немає розробок.
                        </div>
                    </div>
                </div>
            </div>

            <!-- Right Column: Status / Info -->
            <div class="col-md-7 col-lg-8">
                <div class="card h-100" v-if="selectedDraft">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h4 class="card-title m-0">Керування: {{ selectedDraft.component_name }}</h4>
                        <div class="d-flex gap-2">
                            <button class="btn btn-sm btn-outline-danger" @click="deleteDraft(selectedDraft.id)">Видалити</button>
                            <button class="btn btn-sm btn-primary" @click="openInEditor">📂 Відкрити в редакторі</button>
                            <button v-if="!selectedDraft.is_published" class="btn btn-sm btn-success" @click="publishDraft(selectedDraft.id)">🚀 Опублікувати</button>
                        </div>
                    </div>
                    <div class="card-body">
                        <div v-if="selectedDraft.is_published" class="alert alert-success">
                            ✅ Цей додаток вже опубліковано і доступний в системі!
                        </div>
                        <div class="p-4 text-center">
                            <div style="font-size: 3rem;">🛠️</div>
                            <h3 class="mt-3">Додаток готовий до редагування</h3>
                            <p class="text-muted">Натисніть кнопку вище, щоб відкрити код у постійному редакторі. Він залишиться відкритим, навіть якщо ви перейдете в інше вікно.</p>
                        </div>
                    </div>
                </div>
                <div v-else class="card h-100 bg-transparent border-0 d-flex align-items-center justify-content-center text-muted">
                    <div class="text-center">
                        <div style="font-size: 4rem; opacity: 0.5;">🪄</div>
                        <p class="mt-3">Виберіть чернетку зліва або згенеруйте нову, щоб почати роботу.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    props: ['auth'],
    data() {
        return {
            drafts: [],
            selectedDraft: null,
            editorCode: '',
            isGenerating: false,
            newAppName: '',
            newAppPrompt: ''
        }
    },
    mounted() {
        this.fetchDrafts();
    },
    methods: {
        async fetchDrafts() {
            try {
                const res = await fetch('/api/settings/ai-drafts/', { headers: this.auth() });
                if (res.ok) {
                    const data = await res.json();
                    this.drafts = data.results || data;
                }
            } catch (e) {
                console.error("Помилка завантаження чернеток", e);
            }
        },
        selectDraft(draft) {
            this.selectedDraft = draft;
            // No longer using local editorCode
        },
        openInEditor() {
            if (!this.selectedDraft) return;
            this.$root.editorDraftId = this.selectedDraft.id;
            this.$root.isEditorOpen = true;
        },
        async generateApp() {
            this.isGenerating = true;
            try {
                const res = await fetch('/api/settings/ai-builder/generate/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', ...this.auth() },
                    body: JSON.stringify({
                        name: this.newAppName,
                        prompt: this.newAppPrompt
                    })
                });
                
                if (res.ok) {
                    const newDraft = await res.json();
                    this.drafts.unshift(newDraft);
                    this.selectDraft(newDraft);
                    this.openInEditor(); // Auto open after generation
                    this.newAppName = '';
                    this.newAppPrompt = '';
                } else {
                    const error = await res.json();
                    alert(error.error || "Помилка генерації");
                }
            } catch (e) {
                alert("Помилка підключення до AI API. Перевірте чи запущена Ollama.");
            }
            this.isGenerating = false;
        },
        async deleteDraft(id) {
            if (!confirm("Ви впевнені, що хочете видалити цю розробку?")) return;
            try {
                const res = await fetch(`/api/settings/ai-drafts/${id}/`, {
                    method: 'DELETE',
                    headers: this.auth()
                });
                if (res.ok) {
                    if (this.$root.editorDraftId === id) {
                        this.$root.isEditorOpen = false;
                    }
                    this.selectedDraft = null;
                    this.fetchDrafts();
                }
            } catch (e) { }
        },
        async publishDraft(id) {
            if (!confirm("Опублікувати цей додаток? Він стане частиною EME OS.")) return;
            try {
                const res = await fetch(`/api/settings/ai-builder/publish/${id}/`, {
                    method: 'POST',
                    headers: this.auth()
                });
                
                if (res.ok) {
                    alert("Успіх! Додаток опубліковано. Тепер ви можете додати його в App Builder. Оновіть сторінку (F5) для застосування змін.");
                    this.selectedDraft.is_published = true;
                } else {
                    const error = await res.json();
                    alert(error.error || "Помилка публікації");
                }
            } catch (e) {
                alert("Помилка мережі при публікації.");
            }
        }
    }
}
</script>

<style scoped>
.eme-app-title {
    font-size: 1.4rem;
    font-weight: 800;
}
.list-group-item.active {
    background-color: var(--tblr-primary-lt);
    color: var(--tblr-primary);
    border-color: var(--tblr-primary);
}
</style>
