<template>
    <div class="eme-scroll-container">
        <div class="container-fluid py-4 min-vh-100">
            <header class="mb-4 d-flex justify-content-between align-items-center">
                <div class="d-flex align-items-center gap-3">
                    <div class="header-icon-box">🔖</div>
                    <div>
                        <h1 class="page-title m-0">Закладки</h1>
                        <p class="text-muted m-0">Збереження та організація веб-посилань</p>
                    </div>
                </div>
                <!-- Action bar on the right -->
                <button class="btn btn-primary" @click="showAddModal = true">+ Нова закладка</button>
            </header>

            <!-- Search and Filter -->
            <div class="mb-4 d-flex gap-2">
                <input type="text" v-model="searchQuery" class="form-control bg-dark text-white border-secondary" placeholder="Пошук закладок..." style="max-width: 400px;">
                <button class="btn btn-outline-secondary" @click="fetchBookmarks">🔄</button>
            </div>

            <!-- Loading State -->
            <div v-if="isLoading" class="text-center py-5">
                <div class="spinner-border text-info" role="status"></div>
                <div class="mt-2 text-muted">Завантаження закладок...</div>
            </div>

            <!-- Empty State -->
            <div v-else-if="filteredBookmarks.length === 0" class="text-center py-5 empty-state">
                <div class="fs-1 mb-3">📭</div>
                <h3 class="text-white">Немає закладок</h3>
                <p class="text-muted">Збережіть цікаві посилання, щоб вони завжди були під рукою.</p>
                <button class="btn btn-outline-primary mt-3" @click="showAddModal = true">Додати першу закладку</button>
            </div>

            <!-- Bookmarks Grid -->
            <div v-else class="row g-4">
                <div class="col-md-6 col-lg-4" v-for="bm in filteredBookmarks" :key="bm.id">
                    <div class="card bookmark-card h-100">
                        <div class="card-body d-flex flex-column">
                            <div class="d-flex justify-content-between align-items-start mb-2">
                                <h3 class="card-title m-0 text-truncate text-white" :title="bm.title || bm.url">
                                    <a :href="bm.url" target="_blank" rel="noopener noreferrer" class="text-decoration-none text-white hover-info">
                                        {{ bm.title || bm.url }}
                                    </a>
                                </h3>
                                
                                <div class="dropdown">
                                    <button class="btn btn-sm btn-ghost-secondary p-1" data-bs-toggle="dropdown">⋮</button>
                                    <ul class="dropdown-menu dropdown-menu-end dropdown-menu-dark">
                                        <li><a class="dropdown-item text-danger" href="#" @click.prevent="deleteBookmark(bm.id)">Видалити</a></li>
                                    </ul>
                                </div>
                            </div>
                            <a :href="bm.url" target="_blank" class="text-info text-truncate small mb-3 d-block">{{ bm.url }}</a>
                            
                            <p class="text-muted small mb-4 flex-grow-1" style="display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;">
                                {{ bm.description || 'Опис відсутній...' }}
                            </p>
                            
                            <div class="d-flex justify-content-between align-items-center mt-auto pt-3 border-top border-secondary">
                                <div class="d-flex gap-1">
                                    <!-- Badges for tags could go here -->
                                    <span class="badge bg-secondary">Web</span>
                                </div>
                                <small class="text-muted">{{ new Date(bm.created_at).toLocaleDateString() }}</small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Add Modal (Simple overlay for now) -->
            <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
                <div class="eme-modal card bg-dark border-secondary p-4">
                    <h2 class="text-white mb-4">Додати закладку</h2>
                    <form @submit.prevent="saveBookmark">
                        <div class="mb-3">
                            <label class="form-label text-white">URL Посилання *</label>
                            <input type="url" v-model="form.url" class="form-control bg-black text-white border-secondary" required placeholder="https://...">
                        </div>
                        <div class="mb-3">
                            <label class="form-label text-muted">Назва (Залишіть пустим для авто-витягування)</label>
                            <input type="text" v-model="form.title" class="form-control bg-black text-white border-secondary">
                        </div>
                        <div class="mb-4">
                            <label class="form-label text-muted">Опис (Залишіть пустим для авто-витягування)</label>
                            <textarea v-model="form.description" class="form-control bg-black text-white border-secondary" rows="3"></textarea>
                        </div>
                        <div class="d-flex justify-content-end gap-2">
                            <button type="button" class="btn btn-outline-secondary" @click="showAddModal = false">Скасувати</button>
                            <button type="submit" class="btn btn-primary" :disabled="isSaving">
                                {{ isSaving ? 'Збереження...' : 'Зберегти' }}
                            </button>
                        </div>
                    </form>
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
            bookmarks: [],
            isLoading: false,
            searchQuery: '',
            showAddModal: false,
            isSaving: false,
            form: {
                url: '',
                title: '',
                description: ''
            }
        }
    },
    computed: {
        filteredBookmarks() {
            if (!this.searchQuery) return this.bookmarks;
            const q = this.searchQuery.toLowerCase();
            return this.bookmarks.filter(b => 
                (b.title && b.title.toLowerCase().includes(q)) || 
                (b.url && b.url.toLowerCase().includes(q)) ||
                (b.description && b.description.toLowerCase().includes(q))
            );
        }
    },
    methods: {
        async fetchBookmarks() {
            this.isLoading = true;
            try {
                const res = await fetch('/api/utils/bookmarks/', { headers: this.auth() });
                if (res.ok) {
                    const data = await res.json();
                    this.bookmarks = data.results || data;
                }
            } catch (e) {
                console.error(e);
            } finally {
                this.isLoading = false;
            }
        },
        async saveBookmark() {
            this.isSaving = true;
            try {
                const res = await fetch('/api/utils/bookmarks/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', ...this.auth() },
                    body: JSON.stringify(this.form)
                });
                if (res.ok) {
                    this.showAddModal = false;
                    this.form = { url: '', title: '', description: '' };
                    this.fetchBookmarks();
                } else {
                    alert('Помилка при збереженні закладки. Перевірте URL.');
                }
            } catch (e) {
                console.error(e);
            } finally {
                this.isSaving = false;
            }
        },
        async deleteBookmark(id) {
            if (!confirm('Ви впевнені, що хочете видалити цю закладку?')) return;
            try {
                await fetch(`/api/utils/bookmarks/${id}/`, {
                    method: 'DELETE',
                    headers: this.auth()
                });
                this.bookmarks = this.bookmarks.filter(b => b.id !== id);
            } catch (e) {
                console.error(e);
            }
        }
    },
    mounted() {
        this.fetchBookmarks();
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

.bookmark-card {
    background: rgba(26, 28, 46, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    transition: transform 0.2s, box-shadow 0.2s;
}

.bookmark-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 20px rgba(0,0,0,0.4);
    border-color: rgba(0, 229, 255, 0.2);
}

.hover-info:hover {
    color: var(--eme-accent) !important;
}

.modal-overlay {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.8);
    backdrop-filter: blur(5px);
    z-index: 2000;
    display: flex;
    align-items: center;
    justify-content: center;
}

.eme-modal {
    width: 100%;
    max-width: 500px;
    border-radius: 16px;
    box-shadow: 0 20px 40px rgba(0,0,0,0.5);
}
</style>
