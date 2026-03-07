<template>
    <div class="eme-app-page d-flex flex-column h-100">
        <!-- Header -->
        <div class="eme-app-header border-bottom">
            <div class="d-flex align-items-center gap-3">
                <span style="font-size:1.6rem;">📚</span>
                <h1 class="eme-app-title">База Знань</h1>
            </div>
            <div class="d-flex gap-2">
                <div class="input-icon">
                    <input type="text" class="form-control form-control-sm" placeholder="Пошук статей..." v-model="searchQuery">
                </div>
                <!-- Only show 'New Article' if a category is selected or even generally (we can select category in modal) -->
                <button class="btn btn-sm btn-primary" @click="openArticleModal()">+ Стаття</button>
                <button class="btn btn-sm btn-ghost-secondary" @click="$emit('close')">✕</button>
            </div>
        </div>

        <div class="d-flex flex-grow-1 overflow-hidden">
            <!-- Sidebar (Categories) -->
            <div class="kb-sidebar overflow-auto" v-if="!selectedArticle">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h3 class="mb-0 fs-5">Категорії</h3>
                    <button class="btn btn-icon btn-xs btn-ghost-secondary" @click="openCatModal" title="Нова категорія">➕</button>
                </div>
                <div class="nav flex-column nav-pills">
                    <!-- "All" filter -->
                    <a href="#" class="nav-link py-2 mb-1" 
                        :class="{'active': activeCategoryId === null}" 
                        @click.prevent="activeCategoryId = null">
                        🗂️ Всі статті <span class="badge bg-secondary ms-auto">{{ totalArticles }}</span>
                    </a>
                    
                    <a href="#" class="nav-link py-2 mb-1 d-flex align-items-center" 
                        v-for="c in categories" :key="c.id"
                        :class="{'active': activeCategoryId === c.id}"
                        @click.prevent="activeCategoryId = c.id">
                        <span>{{ c.emoji }} {{ c.name }}</span>
                        <span class="badge bg-secondary ms-auto">{{ c.articles_count }}</span>
                    </a>
                </div>
            </div>

            <!-- Main Content Area -->
            <div class="flex-grow-1 d-flex flex-column overflow-hidden kb-content">
                
                <!-- If Loading -->
                <div v-if="loading" class="d-flex justify-content-center align-items-center h-100">
                    <div class="spinner-border text-cyan"></div>
                </div>

                <!-- Article Reader/Editor View -->
                <div v-else-if="selectedArticle" class="d-flex flex-column h-100 w-100">
                    <div class="p-3 border-bottom d-flex align-items-center gap-3 reader-header sticky-top">
                        <button class="btn btn-ghost-secondary btn-sm" @click="selectedArticle = null">← Назад</button>
                        <div class="flex-grow-1">
                            <h2 class="mb-0 fs-3">{{ selectedArticle.title }}</h2>
                            <div class="text-muted small mt-1">
                                <span class="badge bg-blue-lt me-2">{{ selectedArticle.category_emoji }} {{ selectedArticle.category_name }}</span>
                                <span v-if="selectedArticle.tags">🏷️ {{ selectedArticle.tags }}</span>
                            </div>
                        </div>
                        <div>
                            <button class="btn btn-sm btn-outline-primary" @click="openArticleModal(selectedArticle)">✏️ Редагувати</button>
                        </div>
                    </div>
                    <!-- Reader Content -->
                    <div class="overflow-auto flex-grow-1">
                        <div class="reader-content font-serif" v-html="formattedContent"></div>
                    </div>
                </div>

                <!-- Articles List View -->
                <div v-else class="p-4 overflow-auto h-100">
                    <div v-if="filteredArticles.length === 0" class="text-center text-muted mt-5 py-5">
                        <span class="fs-1 d-block mb-3">📭</span>
                        <p>Тут поки порожньо.</p>
                        <button class="btn btn-outline-primary" @click="openArticleModal()">Створити першу статтю</button>
                    </div>
                    
                    <div class="row g-3">
                        <div class="col-md-6 col-lg-4" v-for="a in filteredArticles" :key="a.id">
                            <div class="article-card shadow-sm p-4 d-flex flex-column" @click="selectedArticle = a">
                                <div class="d-flex justify-content-between mb-3">
                                    <span class="badge bg-blue-lt">{{ a.category_emoji }} {{ a.category_name || 'Без категорії' }}</span>
                                </div>
                                <h4 class="mb-3 fs-3 fw-bold">{{ a.title }}</h4>
                                <!-- Preview snippet -->
                                <p class="text-secondary small flex-grow-1 mb-4" style="display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical; overflow: hidden; line-height: 1.5;">
                                    {{ a.content }}
                                </p>
                                <div class="d-flex justify-content-between align-items-center mt-auto pt-3 border-top border-light" style="border-color: rgba(255,255,255,0.05) !important;">
                                    <div class="text-muted small" v-if="a.tags">🏷️ {{ a.tags }}</div>
                                    <div class="text-muted small ms-auto">{{ formatDate(a.updated_at) }}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

            </div>
        </div>

        <!-- Article Edit/Create Modal -->
        <div v-if="modals.article.show" class="eme-modal-overlay" @click.self="modals.article.show = false">
            <div class="eme-modal" style="width: 800px; max-width: 95vw; height: 90vh; display: flex; flex-direction: column;">
                <div class="eme-modal-header">
                    <strong>{{ modals.article.mode === 'new' ? '➕ Нова Стаття' : '✏️ Редагувати Статтю' }}</strong>
                    <button class="btn btn-xs btn-ghost-secondary" @click="modals.article.show = false">✕</button>
                </div>
                <div class="eme-modal-body d-flex flex-column flex-grow-1 overflow-hidden p-3 gap-3">
                    <input class="form-control form-control-lg fs-3" placeholder="Заголовок статті" v-model="modals.article.form.title">
                    
                    <div class="row g-2">
                        <div class="col-6">
                            <select class="form-select" v-model="modals.article.form.category">
                                <option :value="null">Без категорії</option>
                                <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.emoji }} {{ c.name }}</option>
                            </select>
                        </div>
                        <div class="col-6">
                            <input class="form-control" placeholder="Теги (через кому)" v-model="modals.article.form.tags">
                        </div>
                    </div>

                    <textarea class="form-control flex-grow-1 font-monospace" placeholder="Пишіть текст тут (Markdown підтримується)..." v-model="modals.article.form.content"></textarea>
                </div>
                <div class="eme-modal-footer p-3 bg-light border-top d-flex justify-content-between">
                    <button v-if="modals.article.mode === 'edit'" class="btn btn-outline-danger" @click="deleteArticle(modals.article.editId)">🗑 Видалити</button>
                    <div v-else></div>
                    <div class="d-flex gap-2">
                        <button class="btn btn-ghost-secondary" @click="modals.article.show = false">Скасувати</button>
                        <button class="btn btn-primary" :disabled="modals.article.saving" @click="saveArticle">
                            <span v-if="modals.article.saving" class="spinner-border spinner-border-sm me-2"></span>
                            Зберегти
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Category Create Modal -->
        <div v-if="modals.category.show" class="eme-modal-overlay" @click.self="modals.category.show = false">
            <div class="eme-modal" style="width: 400px;">
                <div class="eme-modal-header">
                    <strong>➕ Нова Категорія</strong>
                    <button class="btn btn-xs btn-ghost-secondary" @click="modals.category.show = false">✕</button>
                </div>
                <div class="eme-modal-body p-3">
                    <div class="mb-3 d-flex gap-2">
                        <div style="width: 60px;">
                            <label class="form-label">Emoji</label>
                            <input class="form-control" v-model="modals.category.form.emoji" placeholder="📁">
                        </div>
                        <div class="flex-grow-1">
                            <label class="form-label">Назва</label>
                            <input class="form-control" v-model="modals.category.form.name" placeholder="Моя категорія" @keyup.enter="saveCategory">
                        </div>
                    </div>
                </div>
                <div class="eme-modal-footer p-3 bg-light border-top text-end">
                    <button class="btn btn-primary" @click="saveCategory">Зберегти</button>
                </div>
            </div>
        </div>

    </div>
</template>

<script>
export default {
    props: ['user', 'auth', 'initialArticleId'],
    data() {
        return {
            loading: true,
            categories: [],
            articles: [],
            activeCategoryId: null,
            selectedArticle: null,
            searchQuery: '',

            modals: {
                article: {
                    show: false, mode: 'new', editId: null, saving: false,
                    form: { title: '', content: '', category: null, tags: '' }
                },
                category: {
                    show: false, saving: false,
                    form: { name: '', emoji: '📁' }
                }
            }
        };
    },
    computed: {
        totalArticles() {
            return this.articles.length;
        },
        filteredArticles() {
            let list = this.articles;
            if (this.activeCategoryId) {
                list = list.filter(a => a.category === this.activeCategoryId);
            }
            if (this.searchQuery) {
                const q = this.searchQuery.toLowerCase();
                list = list.filter(a => 
                    a.title.toLowerCase().includes(q) || 
                    a.content.toLowerCase().includes(q)
                );
            }
            return list;
        },
        formattedContent() {
            if (!this.selectedArticle || !this.selectedArticle.content) return '';
            let text = this.selectedArticle.content;
            if (!text.includes('<')) {
                return text.split('\n').map(line => line.trim() ? `<p>${line}</p>` : '<br>').join('');
            }
            return text;
        }
    },
    methods: {
        hdrs() {
            const token = localStorage.getItem('access_token');
            return {
                'Content-Type': 'application/json',
                'Authorization': token ? 'Bearer ' + token : ''
            };
        },
        formatDate(iso) {
            if (!iso) return '';
            const d = new Date(iso);
            return d.toLocaleDateString();
        },
        async fetchData() {
            this.loading = true;
            try {
                const [catRes, artRes] = await Promise.all([
                    fetch('/api/kb/categories/', { headers: this.hdrs() }),
                    fetch('/api/kb/articles/', { headers: this.hdrs() })
                ]);
                const cats = await catRes.json();
                const arts = await artRes.json();
                
                this.categories = cats.results || cats;
                this.articles = arts.results || arts;
            } catch (e) {
                console.error("Failed to load KB data", e);
            } finally {
                this.loading = false;
            }
        },

        // Category Modal
        openCatModal() {
            this.modals.category.form = { name: '', emoji: '📁' };
            this.modals.category.show = true;
        },
        async saveCategory() {
            if (!this.modals.category.form.name.trim()) return;
            try {
                const res = await fetch('/api/kb/categories/', {
                    method: 'POST',
                    headers: this.hdrs(),
                    body: JSON.stringify(this.modals.category.form)
                });
                if (res.ok) {
                    this.modals.category.show = false;
                    await this.fetchData();
                }
            } catch (e) { console.error(e); }
        },

        // Article Modal
        openArticleModal(article = null) {
            if (article) {
                this.modals.article.mode = 'edit';
                this.modals.article.editId = article.id;
                this.modals.article.form = { 
                    title: article.title, 
                    content: article.content, 
                    category: article.category, 
                    tags: article.tags 
                };
            } else {
                this.modals.article.mode = 'new';
                this.modals.article.editId = null;
                this.modals.article.form = { 
                    title: '', 
                    content: '', 
                    category: this.activeCategoryId, // default to active UI category
                    tags: '' 
                };
            }
            this.modals.article.show = true;
        },
        async saveArticle() {
            if (!this.modals.article.form.title.trim()) return;
            this.modals.article.saving = true;
            try {
                const isNew = this.modals.article.mode === 'new';
                const url = isNew ? '/api/kb/articles/' : `/api/kb/articles/${this.modals.article.editId}/`;
                const res = await fetch(url, {
                    method: isNew ? 'POST' : 'PATCH',
                    headers: this.hdrs(),
                    body: JSON.stringify(this.modals.article.form)
                });
                
                if (res.ok) {
                    const savedArt = await res.json();
                    this.modals.article.show = false;
                    await this.fetchData();
                    // Update selected article view if we were editing it
                    if (!isNew && this.selectedArticle && this.selectedArticle.id === this.modals.article.editId) {
                        this.selectedArticle = this.articles.find(a => a.id === savedArt.id) || savedArt;
                    }
                } else {
                    alert("Error saving article: " + JSON.stringify(await res.json()));
                }
            } catch (e) { 
                console.error(e); 
            } finally {
                this.modals.article.saving = false;
            }
        },
        async deleteArticle(id) {
            if (!confirm("Дійсно видалити цю статтю?")) return;
            try {
                await fetch(`/api/kb/articles/${id}/`, { method: 'DELETE', headers: this.hdrs() });
                this.modals.article.show = false;
                this.selectedArticle = null;
                await this.fetchData();
            } catch (e) { console.error(e); }
        }
    },
    async mounted() {
        await this.fetchData();
        if (this.initialArticleId) {
            const art = this.articles.find(a => a.id == this.initialArticleId);
            if (art) this.selectedArticle = art;
        }
    }
}
</script>

<style>
/* EME Variables for consistent experience */
:root {
    --eme-kb-bg: #111422;
    --eme-kb-sidebar: rgba(26, 28, 46, 0.6);
    --eme-kb-card: rgba(255, 255, 255, 0.03);
    --eme-kb-accent: #00e5ff;
}
</style>

<style scoped>
.eme-app-page {
    background: var(--eme-kb-bg);
    color: #e2e8f0;
    min-height: 100vh;
}

.eme-app-header {
    background: rgba(26, 28, 46, 0.8);
    padding: 1.25rem 2rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    display: flex;
    justify-content: space-between;
    align-items: center;
    backdrop-filter: blur(12px);
    position: sticky;
    top: 0;
    z-index: 10;
}

.eme-app-title {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    background: var(--eme-grad);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
}

.kb-sidebar {
    background: var(--eme-kb-sidebar);
    border-right: 1px solid rgba(255, 255, 255, 0.05);
    width: 280px;
    flex-shrink: 0;
    padding: 1.5rem;
    overflow-y: auto;
    backdrop-filter: blur(8px);
}

.kb-content {
    background: transparent;
    flex-grow: 1;
    overflow-y: auto;
    position: relative;
}

.article-card {
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    background: var(--eme-kb-card);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
    height: 100%;
    backdrop-filter: blur(4px);
}

.article-card:hover {
    transform: translateY(-5px);
    background: rgba(255, 255, 255, 0.06);
    border-color: var(--eme-kb-accent);
    box-shadow: 0 15px 30px -10px rgba(0, 229, 255, 0.15);
}

.nav-link {
    border-radius: 10px;
    padding: 0.75rem 1rem;
    color: #94a3b8;
    font-weight: 500;
    transition: all 0.2s;
    margin-bottom: 4px;
}

.nav-link:hover {
    background: rgba(255, 255, 255, 0.05);
    color: #f1f5f9;
}

.nav-link.active {
    background: rgba(0, 229, 255, 0.1);
    color: var(--eme-kb-accent);
    font-weight: 600;
    border: 1px solid rgba(0, 229, 255, 0.2);
}

.reader-content {
    max-width: 850px;
    margin: 0 auto;
    font-size: 1.15rem;
    line-height: 1.8;
    color: #cbd5e1;
    padding: 4rem 2rem;
}

.reader-header {
    background: rgba(255, 255, 255, 0.02);
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
}

/* Custom form styling to match theme */
.form-control, .form-select {
    background: rgba(0, 0, 0, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: white;
    border-radius: 10px;
}

.form-control:focus, .form-select:focus {
    background: rgba(0, 0, 0, 0.3);
    border-color: var(--eme-kb-accent);
    box-shadow: 0 0 0 3px rgba(0, 229, 255, 0.1);
    color: white;
}

.badge.bg-blue-lt {
    background: rgba(59, 130, 246, 0.1) !important;
    color: #60a5fa !important;
    border: 1px solid rgba(59, 130, 246, 0.2);
}

@media (max-width: 768px) {
    .kb-sidebar {
        display: none;
    }
}
</style>
