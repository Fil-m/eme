<template>
    <div class="eme-app-page">
        <!-- Visiting Alert -->
        <div v-if="visitingUser" class="alert alert-info border-0 shadow-sm mb-4 py-2" style="background: rgba(0, 229, 255, 0.05);">
            <div class="d-flex align-items-center justify-content-between">
                <span class="small">🌐 Ви переглядаєте профіль: <b>{{ visitingUser.username }}</b></span>
                <button class="btn btn-sm btn-primary py-0" style="font-size: 11px;" @click="$emit('return')">До себе</button>
            </div>
        </div>

        <div class="eme-app-header">
            <h1 class="eme-app-title">Профіль</h1>
            <button class="btn btn-sm btn-ghost-secondary px-2" @click="$emit('close')">✕</button>
        </div>

        <!-- Hero Card (Upper Info) -->
        <div class="card mb-3 border-0 shadow-sm overflow-hidden" style="background: var(--tblr-card-bg); border-radius: 16px;">
            <div class="card-cover" style="height: 120px; background: var(--eme-grad); opacity: 0.15;"></div>
            <div class="card-body pt-0 px-4 pb-4">
                <div class="d-flex align-items-end gap-4" style="margin-top: -40px;">
                    <div class="eme-avatar shadow-lg position-relative cursor-pointer hover-edit" 
                        style="width:110px; height:110px; font-size:2.8rem; border-width: 4px; background: var(--tblr-card-bg);"
                        @click="triggerAvatarUpload">
                        <img v-if="currentUser.avatar" :src="currentUser.avatar">
                        <span v-else>{{ (currentUser.first_name || currentUser.username || 'U')[0].toUpperCase() }}</span>
                        
                        <!-- Overlay on hover (only for owner) -->
                        <div v-if="!visitingUser || (visitingUser && user.id === visitingUser.id)" class="avatar-edit-overlay">
                            <i v-if="uploading" class="spinner-border spinner-border-sm"></i>
                            <i v-else class="ti ti-camera"></i>
                        </div>
                        <input type="file" ref="avatarInput" class="d-none" accept="image/*" @change="uploadAvatar">
                    </div>
                    <div class="pb-2">
                        <h2 class="mb-1 fw-bold" style="font-size:1.8rem; color: #fff;">{{ currentUser.first_name || currentUser.username }}</h2>
                        <div class="d-flex align-items-center gap-2">
                            <span class="text-muted small">@{{ currentUser.username }}</span>
                            <span class="eme-xp-badge">LVL {{ currentUser.level }}</span>
                        </div>
                    </div>
                </div>
                
                <div class="mt-4 row g-3">
                    <div class="col-md-8">
                        <p v-if="currentUser.bio" class="mb-2 text-secondary" style="white-space: pre-wrap;">{{ currentUser.bio }}</p>
                        <div class="d-flex flex-wrap gap-3 small text-muted">
                            <span v-if="currentUser.address"><i class="ti ti-map-pin me-1"></i> {{ currentUser.address }}</span>
                            <span v-if="currentUser.social_links && currentUser.social_links.length" v-for="s in currentUser.social_links" class="text-info">
                                <i class="ti ti-link me-1"></i> {{ s.network_name }}
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- TAB NAVIGATION -->
        <div class="d-flex border-bottom mb-4 profile-tabs">
            <button v-for="t in tabs" :key="t.id" 
                class="btn-tab" 
                :class="{ active: activeTab === t.id }"
                @click="activeTab = t.id"
            >
                {{ t.emoji }} {{ t.name }}
            </button>
        </div>

        <!-- CONTENT AREA -->
        <div class="tab-content">
            <!-- 1. WALL -->
            <div v-if="activeTab === 'wall'" class="animate__animated animate__fadeIn">
                <!-- Write Post -->
                <div v-if="!visitingUser || (visitingUser && user.id === visitingUser.id)" class="card mb-3 border-0 shadow-sm" style="background: rgba(255,255,255,0.03); border-radius: 12px;">
                    <div class="card-body p-3">
                        <div class="d-flex gap-2">
                            <div class="avatar avatar-sm rounded-circle">
                                <img v-if="user.avatar" :src="user.avatar">
                                <span v-else>{{ user.username[0].toUpperCase() }}</span>
                            </div>
                            <div class="flex-grow-1">
                                <textarea v-model="newPost" class="form-control bg-transparent border-0 text-white p-2" 
                                    rows="1" placeholder="Що у вас нового?"
                                    style="resize: none; overflow: hidden;"
                                    @focus="$event.target.rows = 3"
                                ></textarea>
                                <div v-if="newPost" class="d-flex justify-content-end mt-2 animate__animated animate__fadeIn">
                                    <button class="btn btn-primary btn-sm px-4" @click="sendPost" :disabled="!newPost.trim() || loading">
                                        Надіслати
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Posts List -->
                <div v-if="wallPosts.length" class="d-flex flex-column gap-3">
                    <div v-for="post in wallPosts" :key="post.id" class="card border-0 shadow-sm wall-post" style="background: var(--tblr-card-bg);">
                        <div class="card-body p-3">
                            <div class="d-flex gap-3 mb-2">
                                <div class="avatar avatar-md rounded-circle">
                                    <img v-if="post.author_avatar" :src="post.author_avatar">
                                    <span v-else>{{ post.author_name[0].toUpperCase() }}</span>
                                </div>
                                <div class="flex-grow-1">
                                    <div class="fw-bold text-white">{{ post.author_name }}</div>
                                    <div class="text-muted" style="font-size: 11px;">{{ formatDate(post.created_at) }}</div>
                                </div>
                                <button v-if="post.author === user.id" class="btn btn-sm btn-ghost-danger p-1" @click="deletePost(post.id)">✕</button>
                            </div>
                            <div class="post-content mb-3" style="font-size: 14px; white-space: pre-wrap; color: #cbd5e1;">{{ post.content }}</div>
                            <div class="d-flex gap-3 border-top pt-2" style="border-color: rgba(255,255,255,0.05) !important;">
                                <button class="btn btn-ghost-secondary btn-sm px-2">❤️ {{ post.likes_count || '' }}</button>
                                <button class="btn btn-ghost-secondary btn-sm px-2" @click="toggleComments(post.id)">💬 {{ post.comments?.length || '' }}</button>
                            </div>

                            <!-- Comments Section -->
                            <div v-if="commentingId === post.id" class="mt-3 ps-4 border-start" style="border-width: 2px !important; border-color: var(--eme-accent) !important;">
                                <div v-for="comm in post.comments" :key="comm.id" class="mb-2 small">
                                    <span class="fw-bold text-info">@{{ comm.author_name }}:</span> 
                                    <span class="text-secondary">{{ comm.content }}</span>
                                </div>
                                <div class="mt-2 d-flex gap-2">
                                    <input v-model="newComment" class="form-control form-control-sm bg-dark border-secondary text-white" 
                                        placeholder="Коментувати..." @keyup.enter="sendComment(post.id)">
                                    <button class="btn btn-primary btn-sm" @click="sendComment(post.id)">📝</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div v-else class="text-center py-5 text-muted">
                    <div style="font-size: 3rem; opacity: 0.3;">📭</div>
                    <p class="mt-2">На стіні поки що тихо...</p>
                </div>
            </div>

            <!-- 2. PROJECTS -->
            <div v-if="activeTab === 'projects'" class="animate__animated animate__fadeIn">
                <div v-if="projects.length" class="row g-3">
                    <div v-for="p in projects" :key="p.id" class="col-md-6">
                        <div class="card border-0 shadow-sm" style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05) !important;">
                            <div class="card-body p-3">
                                <div class="d-flex align-items-center gap-2 mb-2">
                                    <span style="font-size:1.5rem;">{{ p.emoji || '🏗️' }}</span>
                                    <h3 class="card-title m-0 text-white">{{ p.title }}</h3>
                                </div>
                                <p class="text-muted small mb-3">{{ p.description }}</p>
                                <div class="d-flex justify-content-between align-items-center">
                                    <span class="badge bg-blue-lt">Project</span>
                                    <span class="text-muted" style="font-size: 10px;">{{ formatDate(p.created_at) }}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div v-else class="text-center py-5 text-muted">Публічних проектів не знайдено</div>
            </div>

            <!-- 3. GALLERY -->
            <div v-if="activeTab === 'gallery'" class="animate__animated animate__fadeIn">
                <div v-if="gallery.length" class="row g-2">
                    <div v-for="img in gallery" :key="img.id" class="col-4 col-md-3">
                        <div class="ratio ratio-1x1 rounded-3 overflow-hidden shadow-sm border border-white-5" style="cursor: pointer; background: rgba(255,255,255,0.05);">
                            <img :src="img.preview_url || img.file_url || img.file" class="object-cover w-100 h-100" @click="openMedia(img)" onerror="this.src='https://placehold.co/300?text=No+Preview'">
                        </div>
                    </div>
                </div>
                <div v-else class="text-center py-5 text-muted">
                    <div style="font-size:3rem; opacity:0.1;">🖼️</div>
                    <p class="mt-2 small">Публічних фото не знайдено</p>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    props: ['user', 'visitingUser', 'auth'],
    data() {
        return {
            activeTab: 'wall',
            tabs: [
                { id: 'wall', name: 'Стіна', emoji: '📢' },
                { id: 'projects', name: 'Проекти', emoji: '🏗️' },
                { id: 'gallery', name: 'Галерея', emoji: '🖼️' },
            ],
            wallPosts: [],
            projects: [],
            gallery: [],
            newPost: '',
            newComment: '',
            commentingId: null,
            loading: false,
            uploading: false
        }
    },
    computed: {
        currentUser() {
            return this.visitingUser || this.user;
        }
    },
    watch: {
        activeTab: {
            immediate: true,
            handler(newTab) {
                if (newTab === 'wall') this.loadWall();
                if (newTab === 'projects') this.loadProjects();
                if (newTab === 'gallery') this.loadGallery();
            }
        },
        'currentUser.id': {
            immediate: true,
            handler() {
                this.loadWall();
            }
        }
    },
    methods: {
        formatDate(dateStr) {
            if (!dateStr) return '';
            const d = new Date(dateStr);
            return d.toLocaleDateString('uk-UA') + ' ' + d.toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' });
        },
        async loadWall() {
            if (!this.currentUser?.id) return;
            try {
                // Add timestamp to prevent caching
                const res = await fetch(`/api/profiles/wall-posts/?owner=${this.currentUser.id}&t=${Date.now()}`, { headers: this.auth() });
                if (res.ok) {
                    const data = await res.json();
                    this.wallPosts = data.results || data;
                }
            } catch (e) {}
        },
        async loadProjects() {
            if (!this.currentUser?.id) return;
            try {
                const res = await fetch(`/api/projects/?owner=${this.currentUser.id}&t=${Date.now()}`, { headers: this.auth() });
                if (res.ok) {
                    const data = await res.json();
                    this.projects = data.results || data;
                }
            } catch (e) {}
        },
        async loadGallery() {
            if (!this.currentUser?.id) return;
            try {
                const res = await fetch(`/api/media/files/?user_id=${this.currentUser.id}&mime_type=image&t=${Date.now()}`, { headers: this.auth() });
                if (res.ok) {
                    const data = await res.json();
                    this.gallery = data.results || data;
                }
            } catch (e) {}
        },
        async sendPost() {
            if (!this.newPost.trim()) return;
            this.loading = true;
            try {
                const res = await fetch('/api/profiles/wall-posts/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', ...this.auth() },
                    body: JSON.stringify({
                        owner: this.currentUser.id,
                        content: this.newPost
                    })
                });
                if (res.ok) {
                    this.newPost = '';
                    this.loadWall();
                } else {
                    const err = await res.json();
                    alert("Помилка публікації: " + (err.detail || JSON.stringify(err)));
                }
            } catch (e) {
                alert("Помилка мережі при спробі опублікувати пост");
            } finally {
                this.loading = false;
            }
        },
        async deletePost(id) {
            if (!confirm('Видалити цей пост?')) return;
            try {
                const res = await fetch(`/api/profiles/wall-posts/${id}/`, {
                    method: 'DELETE',
                    headers: this.auth()
                });
                if (res.ok) this.loadWall();
            } catch (e) {}
        },
        toggleComments(postId) {
            this.commentingId = this.commentingId === postId ? null : postId;
            this.newComment = '';
        },
        async sendComment(postId) {
            if (!this.newComment.trim()) return;
            try {
                const res = await fetch('/api/profiles/wall-comments/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', ...this.auth() },
                    body: JSON.stringify({
                        post: postId,
                        content: this.newComment
                    })
                });
                if (res.ok) {
                    this.newComment = '';
                    this.loadWall();
                }
            } catch (e) {}
        },
        triggerAvatarUpload() {
            if (this.visitingUser && this.visitingUser.id !== this.user.id) return;
            this.$refs.avatarInput.click();
        },
        async uploadAvatar(event) {
            const file = event.target.files[0];
            if (!file) return;

            this.uploading = true;
            const formData = new FormData();
            formData.append('avatar', file);

            try {
                const res = await fetch('/api/profiles/me/avatar/', {
                    method: 'PATCH',
                    headers: { ...this.auth() },
                    body: formData
                });
                if (res.ok) {
                    const data = await res.json();
                    this.$emit('refresh-user');
                    // Ensure local update
                    setTimeout(() => {
                        this.$emit('update-user-avatar', data.avatar);
                    }, 100);
                }
            } catch (e) {
                console.error("Avatar upload failed", e);
            } finally {
                this.uploading = false;
            }
        },
        openMedia(img) {
            const url = img.file_url || img.file || `/api/media/files/${img.id}/stream/`;
            window.open(url, '_blank');
        }
    }
}
</script>

<style scoped>
.btn-tab {
    padding: 12px 24px;
    border: none;
    background: transparent;
    color: var(--tblr-secondary);
    font-weight: 600;
    font-size: 14px;
    border-bottom: 2px solid transparent;
    transition: 0.2s;
}

.btn-tab.active {
    color: var(--eme-accent);
    border-bottom-color: var(--eme-accent);
}

.btn-tab:hover {
    background: rgba(0, 229, 255, 0.05);
}

.eme-avatar {
    border: 3px solid var(--eme-accent);
    border-radius: 50%;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--eme-accent);
}

.eme-avatar img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.eme-xp-badge {
    padding: 2px 8px;
    background: rgba(0, 229, 255, 0.1);
    border: 1px solid rgba(0, 229, 255, 0.2);
    border-radius: 20px;
    font-size: 10px;
    color: var(--eme-accent);
    font-weight: bold;
}

.eme-app-title {
    font-size: 1.5rem;
    font-weight: 800;
    background: var(--eme-grad);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
}

.profile-tabs {
    position: sticky;
    top: -1px;
    background: var(--tblr-body-bg);
    z-index: 10;
}

.wall-post {
    border: 1px solid rgba(255,255,255,0.05) !important;
    border-radius: 12px;
}

.avatar-edit-overlay {
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0,0,0,0.3);
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0.6;
    transition: 0.2s;
    color: white;
    font-size: 1.5rem;
}

.hover-edit:hover .avatar-edit-overlay {
    opacity: 1;
    background: rgba(0,0,0,0.5);
}

.cursor-pointer {
    cursor: pointer;
}

.object-cover {
    object-fit: cover;
}
</style>
