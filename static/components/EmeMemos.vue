<template>
    <div class="eme-scroll-container">
        <div class="container-fluid py-4 min-vh-100">
            <header class="mb-4 d-flex justify-content-between align-items-center">
                <div class="d-flex align-items-center gap-3">
                    <div class="header-icon-box">📝</div>
                    <div>
                        <h1 class="page-title m-0">Нотатки</h1>
                        <p class="text-muted m-0">Швидкі мікро-записи та нагадування</p>
                    </div>
                </div>
            </header>

            <div class="row g-4">
                <!-- Left Sidebar: Filter / Tags -->
                <div class="col-md-3">
                    <div class="card bg-dark border-secondary h-100 p-3">
                        <input type="text" v-model="searchQuery" class="form-control bg-black text-white border-secondary mb-3" placeholder="Пошук нотаток...">
                        
                        <!-- Mini tags list could go here in the future -->
                        <div class="text-muted small">Всього нотаток: {{ filteredMemos.length }}</div>
                    </div>
                </div>

                <!-- Main Memo Area -->
                <div class="col-md-9">
                    <!-- Create Note Editor -->
                    <div class="card bg-dark border-secondary mb-4 p-3 shadow-lg create-card" :class="{ 'focused': isCreating }">
                        <textarea v-model="newMemoContent" class="form-control bg-black text-white border-secondary mb-3 memo-textarea" 
                                  placeholder="Про що ви думаєте? Запишіть сюди..." 
                                  @focus="isCreating = true" rows="4"></textarea>
                        
                        <div class="d-flex justify-content-between align-items-center" v-show="isCreating || newMemoContent">
                            <div class="form-check form-switch cursor-pointer">
                                <input class="form-check-input" type="checkbox" v-model="newMemoPinned" id="pinSwitch">
                                <label class="form-check-label text-warning" for="pinSwitch">📌 Закріпити нагорі</label>
                            </div>
                            <div class="d-flex gap-2">
                                <button class="btn btn-outline-secondary" @click="cancelCreate" v-if="isCreating && !newMemoContent">Скасувати</button>
                                <button class="btn btn-primary" :disabled="!newMemoContent" @click="saveMemo">Зберегти</button>
                            </div>
                        </div>
                    </div>

                    <!-- Memos List -->
                    <div class="memos-list d-flex flex-column gap-3">
                        <div v-if="filteredMemos.length === 0" class="text-center text-muted py-5">
                            Відсутні записи. Створіть першу нотатку вище.
                        </div>

                        <div v-for="memo in filteredMemos" :key="memo.id" class="card memo-card bg-dark border-secondary">
                            <div class="card-body position-relative">
                                <!-- Pin Icon -->
                                <div v-if="memo.is_pinned" class="position-absolute top-0 end-0 p-2 text-warning" title="Закріплено">📌</div>
                                
                                <p class="memo-content text-white">{{ memo.content }}</p>
                                
                                <div class="d-flex justify-content-between align-items-center mt-3 pt-3 border-top border-secondary opacity-50 memo-footer">
                                    <small>{{ new Date(memo.created_at).toLocaleString('uk-UA') }}</small>
                                    <div class="d-flex gap-2">
                                        <button class="btn btn-sm btn-ghost-secondary p-1" @click="togglePin(memo)">
                                            {{ memo.is_pinned ? 'Відкріпити' : 'Закріпити' }}
                                        </button>
                                        <button class="btn btn-sm btn-ghost-danger p-1" @click="deleteMemo(memo.id)">Видалити</button>
                                    </div>
                                </div>
                            </div>
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
            memos: [],
            newMemoContent: '',
            newMemoPinned: false,
            isCreating: false,
            searchQuery: ''
        }
    },
    computed: {
        filteredMemos() {
            if (!this.searchQuery) return this.memos;
            const q = this.searchQuery.toLowerCase();
            return this.memos.filter(m => m.content && m.content.toLowerCase().includes(q));
        }
    },
    methods: {
        async fetchMemos() {
            try {
                const res = await fetch('/api/utils/memos/', { headers: this.auth() });
                if (res.ok) {
                    const data = await res.json();
                    this.memos = data.results || data;
                }
            } catch (e) { console.error('Error fetching memos', e); }
        },
        async saveMemo() {
            if (!this.newMemoContent.trim()) return;
            try {
                const res = await fetch('/api/utils/memos/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', ...this.auth() },
                    body: JSON.stringify({
                        content: this.newMemoContent,
                        is_pinned: this.newMemoPinned
                    })
                });
                if (res.ok) {
                    this.newMemoContent = '';
                    this.newMemoPinned = false;
                    this.isCreating = false;
                    this.fetchMemos();
                } else {
                    alert('Помилка при збереженні нотатки.');
                }
            } catch (e) { console.error(e); }
        },
        async togglePin(memo) {
            try {
                await fetch(`/api/utils/memos/${memo.id}/`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json', ...this.auth() },
                    body: JSON.stringify({ is_pinned: !memo.is_pinned })
                });
                this.fetchMemos();
            } catch (e) { console.error(e); }
        },
        async deleteMemo(id) {
            if (!confirm('Видалити нотатку?')) return;
            try {
                await fetch(`/api/utils/memos/${id}/`, {
                    method: 'DELETE',
                    headers: this.auth()
                });
                this.memos = this.memos.filter(m => m.id !== id);
            } catch (e) { console.error(e); }
        },
        cancelCreate() {
            this.isCreating = false;
            this.newMemoContent = '';
            this.newMemoPinned = false;
        }
    },
    mounted() {
        this.fetchMemos();
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

.create-card {
    transition: all 0.3s ease;
    border: 1px solid rgba(0, 229, 255, 0.1);
}

.create-card.focused {
    border-color: var(--eme-accent);
    box-shadow: 0 10px 30px rgba(0, 229, 255, 0.1) !important;
}

.memo-textarea {
    resize: none;
    font-size: 1.1rem;
}

.memo-card {
    transition: transform 0.2s, box-shadow 0.2s;
}

.memo-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(0,0,0,0.3);
}

.memo-content {
    white-space: pre-wrap;
    font-size: 1.1rem;
    line-height: 1.5;
    margin-bottom: 0px;
}

.memo-footer {
    transition: opacity 0.2s;
}
.memo-card:hover .memo-footer {
    opacity: 1 !important;
}
</style>
