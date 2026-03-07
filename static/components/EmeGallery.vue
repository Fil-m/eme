<template>
    <div class="eme-app-page">
        <div v-if="visitingUser" class="alert alert-info bg-primary-lt border-primary mb-3 py-2">
            <div class="d-flex align-items-center justify-content-between">
                <span>🌐 Ви переглядаєте файли користувача <b>{{ visitingUser.username }}</b></span>
                <button class="btn btn-sm btn-primary" @click="$emit('return')">Повернутись до
                    себе</button>
            </div>
        </div>

        <!-- Merged Header (FIXED) -->
        <div class="eme-app-header">
            <div class="d-flex align-items-center gap-3">
                <h1 class="eme-app-title">Галерея</h1>
                <div class="nav nav-tabs border-0 mt-1">
                    <button class="nav-link bg-transparent border-0 px-2 active">Медіатека</button>
                </div>
            </div>
            <div class="d-flex gap-2">
                <button v-if="activeCollection && currentTab==='gallery'" class="btn btn-sm btn-outline-secondary"
                    @click="activeCollection = null">← Назад</button>
                <button v-if="!visitingUser && currentTab==='gallery'" class="btn btn-sm btn-primary"
                    @click="showNewCollectionModal=true">+ Створити папку</button>
                <button class="btn btn-sm btn-ghost-secondary" @click="$emit('close')">✕</button>
            </div>
        </div>

        <div v-if="currentTab === 'gallery'">
            <!-- Collections Header -->
        <div v-if="!activeCollection" class="row g-3 mb-4">
            <div v-for="col in collections" :key="col.id" class="col-md-3">
                <div class="card card-stacked card-link" @click="activeCollection = col">
                    <div class="card-body text-center py-4">
                        <div style="font-size:2.5rem;margin-bottom:8px;">📁</div>
                        <div class="fw-bold text-truncate">{{ col.name }}</div>
                        <div class="text-muted small">{{ col.file_count }} файлів</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- New Collection Dialog -->
        <div v-if="showNewCollectionModal" class="modal modal-blur fade show d-block"
            style="background:rgba(0,0,0,0.5); z-index: 1050;">
            <div class="modal-dialog modal-sm modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5>Нова папка</h5>
                    </div>
                    <div class="modal-body">
                        <input type="text" class="form-control" v-model="newCollectionName"
                            placeholder="Назва папки..." @keyup.enter="createCollection">
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-link link-secondary"
                            @click="showNewCollectionModal=false">Скасувати</button>
                        <button class="btn btn-primary" @click="createCollection" :disabled="!newCollectionName">Створити</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Files View -->
        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <strong>{{ activeCollection ? activeCollection.name : 'Усі файли' }}</strong>
                <div class="btn-group">
                    <button class="btn btn-sm btn-icon" :class="{'btn-primary': viewMode==='grid'}"
                        @click="viewMode='grid'">▦</button>
                    <button class="btn btn-sm btn-icon" :class="{'btn-primary': viewMode==='list'}"
                        @click="viewMode='list'">☰</button>
                </div>
            </div>
            <div class="card-body p-0">
                <!-- Table View -->
                <div v-if="viewMode === 'list'" class="table-responsive">
                    <table class="table table-vcenter card-table">
                        <thead>
                            <tr>
                                <th>Ім'я</th>
                                <th>Розмір</th>
                                <th>Дата</th>
                                <th class="w-1"></th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="file in files" :key="file.id" @click="openLightbox(file)"
                                style="cursor:pointer">
                                <td>
                                    <div class="d-flex align-items-center gap-2">
                                        <span v-if="file.is_image">🖼️</span>
                                        <span v-else-if="file.is_video">🎬</span>
                                        <span v-else>📄</span>
                                        <div class="text-truncate" style="max-width:260px;">{{ file.file_name }}</div>
                                    </div>
                                </td>
                                <td class="text-muted">{{ (file.file_size / 1024 / 1024).toFixed(2) }} MB</td>
                                <td class="text-muted">{{ new Date(file.created_at).toLocaleDateString() }}</td>
                                <td>
                                    <div class="d-flex gap-1" @click.stop>
                                        <button class="btn btn-sm btn-icon btn-ghost-primary"
                                            @click.stop="downloadMedia(file.id)">⬇</button>
                                        <button v-if="!visitingUser"
                                            class="btn btn-sm btn-icon btn-ghost-danger"
                                            @click.stop="deleteFile(file.id)">🗑</button>
                                    </div>
                                </td>
                            </tr>
                            <tr v-if="!files.length">
                                <td colspan="4" class="text-center py-4 text-muted">Немає файлів у цій папці</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <!-- Grid View -->
                <div v-if="viewMode === 'grid'" class="p-3">
                    <div class="row g-3">
                        <div v-for="file in files" :key="file.id" class="col-6 col-md-3 col-lg-2">
                            <div class="card card-sm card-hover" @click="openLightbox(file)"
                                style="cursor:pointer">
                                <div class="card-img-top img-responsive img-responsive-1x1"
                                    :style="file.is_image ? 'background-image: url(' + getMediaUrl(file.file || file.file_path) + ')' : ''">
                                    <div v-if="!file.is_image"
                                        class="d-flex align-items-center justify-content-center h-100 bg-light-lt">
                                        <span v-if="file.is_video" style="font-size:2rem;">🎬</span>
                                        <span v-else style="font-size:2rem;">📄</span>
                                    </div>
                                </div>
                                <div class="card-body p-2">
                                    <div class="text-truncate small fw-bold">{{ file.file_name }}</div>
                                    <div class="d-flex justify-content-between mt-1">
                                        <span class="text-muted" style="font-size:10px;">{{ (file.file_size/1024/1024).toFixed(1) }}M</span>
                                        <button v-if="!visitingUser"
                                            class="btn btn-icon btn-sm btn-ghost-danger p-0 border-0"
                                            style="height:12px;width:12px;" title="Видалити"
                                            @click.stop="deleteFile(file.id)">🗑</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Lightbox -->
        <div v-if="lightboxMedia" class="modal modal-blur fade show d-block"
            style="background: rgba(0,0,0,0.8); z-index: 9999;" @click.self="lightboxMedia = null">
            <div class="modal-dialog modal-lg modal-dialog-centered">
                <div class="modal-content border-0 bg-transparent">
                    <div class="modal-header border-0 p-2 justify-content-end">
                        <button class="btn btn-icon btn-ghost-light" @click="lightboxMedia = null">✕</button>
                    </div>
                    <div class="modal-body p-0 text-center">
                        <img v-if="lightboxMedia.is_image"
                            :src="getMediaUrl(lightboxMedia.file || lightboxMedia.file_path)"
                            class="img-fluid rounded shadow">
                        <video v-else-if="lightboxMedia.is_video" controls class="w-100 rounded shadow" autoplay>
                            <source :src="getMediaUrl(lightboxMedia.file || lightboxMedia.file_path)"
                                :type="lightboxMedia.mime_type">
                        </video>
                        <div v-else class="bg-dark p-5 rounded d-inline-block text-white">
                            <div style="font-size:4rem;">📄</div>
                            <div class="mt-3">{{ lightboxMedia.file_name }}</div>
                            <button class="btn btn-primary mt-3" @click="downloadMedia(lightboxMedia.id)">Download File</button>
                        </div>
                        <div class="mt-3 text-white fw-bold">{{ lightboxMedia.file_name }}</div>
                        <div class="text-muted small">{{ (lightboxMedia.file_size / 1024 / 1024).toFixed(2) }} MB • {{ lightboxMedia.mime_type }}</div>
                    </div>
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
            files: [],
            collections: [],
            activeCollection: null,
            viewMode: 'grid',
            localFilePath: '',
            showNewCollectionModal: false,
            newCollectionName: '',
            lightboxMedia: null
        }
    },
    mounted() {
        if (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
            this.currentTab = 'explorer';
            this.fetchExplorer();
        }
        this.fetchFiles();
    },
    watch: {
        activeCollection() {
            this.fetchFiles();
        },
        visitingUser: {
            immediate: true,
            handler() {
                this.fetchFiles();
            }
        }
    },
    methods: {
        async fetchFiles() {
            let url = '/api/media/files/';
            if (this.activeCollection) {
                url += `?collection=${this.activeCollection.id}`;
            } else if (this.visitingUser) {
                url += `?user=${this.visitingUser.id}`;
            }

            try {
                const [fRes, cRes] = await Promise.all([
                    fetch(url, { headers: this.auth() }),
                    fetch('/api/media/collections/' + (this.visitingUser ? `?user=${this.visitingUser.id}` : ''), { headers: this.auth() })
                ]);
                const fData = await fRes.json();
                this.files = fData.results || fData;
                
                const cData = await cRes.json();
                this.collections = cData.results || cData;
            } catch (e) { }
        },
        async createCollection() {
            if (!this.newCollectionName) return;
            try {
                const res = await fetch('/api/media/collections/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', ...this.auth() },
                    body: JSON.stringify({ name: this.newCollectionName })
                });
                if (res.ok) {
                    this.newCollectionName = '';
                    this.showNewCollectionModal = false;
                    this.fetchFiles();
                }
            } catch (e) { }
        },
        async deleteFile(id) {
            if (!confirm('Видалити цей файл?')) return;
            try {
                const res = await fetch(`/api/media/files/${id}/`, {
                    method: 'DELETE',
                    headers: this.auth()
                });
                if (res.ok) this.fetchFiles();
            } catch (e) { }
        },
        downloadMedia(id) {
            window.open(`/api/media/files/${id}/stream/`, '_blank');
        },
        getMediaUrl(url) {
            if (!url) return '';
            if (url.startsWith('http')) return url;
            return url;
        },
        openLightbox(file) {
            this.lightboxMedia = file;
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

@media (max-width: 768px) {
    .eme-app-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 12px;
        margin-bottom: 16px;
    }
    
    .nav-tabs {
        width: 100%;
        justify-content: flex-start;
    }
    
    .eme-app-title {
        font-size: 1.2rem;
    }

    .card-body {
        padding: 12px;
    }
}
</style>
