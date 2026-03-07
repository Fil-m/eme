<template>
    <div class="eme-app-page">
        <!-- Merged Header -->
        <div class="eme-app-header">
            <div class="d-flex align-items-center gap-3">
                <h1 class="eme-app-title">Індексатор</h1>
            </div>
            <div class="d-flex gap-2">
                <button class="btn btn-sm btn-outline-secondary" @click="fetchExplorer('..')">Вгору ↑</button>
                <button class="btn btn-sm btn-ghost-secondary" @click="$emit('close')">✕</button>
            </div>
        </div>

        <div class="row g-3 mb-4">
            <div class="col-md-6">
                <!-- Select Collection -->
                <div class="card mb-3">
                    <div class="card-header d-flex justify-content-between">
                        <strong class="small uppercase text-muted">Вибір папки (Опційно)</strong>
                    </div>
                    <div class="card-body py-3">
                        <select class="form-select form-select-sm" v-model="activeCollectionId">
                            <option :value="null">Без папки (Root)</option>
                            <option v-for="c in collections" :key="c.id" :value="c.id">{{ c.name }}</option>
                        </select>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header d-flex justify-content-between">
                        <strong class="small uppercase text-muted">Завантаження</strong>
                    </div>
                    <div class="card-body py-3">
                        <label class="btn btn-outline-primary w-100 mb-0 d-flex align-items-center justify-content-center gap-2">
                            <span>📂 Обрати файли...</span>
                            <input type="file" multiple class="d-none" @change="uploadFiles">
                        </label>
                        <div class="text-center mt-2 small text-muted d-none d-md-block">або перетягніть сюди</div>
                    </div>
                </div>
            </div>

            <div class="col-md-6">
                <div class="card h-100">
                    <div class="card-header"><strong class="small uppercase text-muted">Індексація шляху (Local Path)</strong></div>
                    <div class="card-body py-3 d-flex flex-column justify-content-center">
                        <div class="input-group">
                            <input type="text" class="form-control form-control-sm"
                                placeholder="D:\media\video.mp4" v-model="localFilePath" @keyup.enter="indexLocalFile">
                            <button class="btn btn-sm btn-primary" @click="indexLocalFile">Індексувати</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- EXPLORER TAB -->
        <div class="eme-explorer">
            <div class="card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <div class="d-flex align-items-center gap-2 text-truncate">
                        <strong class="small uppercase text-muted">Шлях:</strong>
                        <span class="font-monospace small text-primary text-truncate">{{ explorerPath }}</span>
                    </div>
                </div>
                <div class="table-responsive" style="max-height:600px;">
                    <table class="table table-vcenter table-nowrap card-table">
                        <thead>
                            <tr>
                                <th>Назва</th>
                                <th class="w-1">Розмір</th>
                                <th class="w-1">Дія</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-if="!explorerItems.length">
                                <td colspan="3" class="text-center py-4 text-muted small">
                                    Папка порожня або доступ заборонено
                                </td>
                            </tr>
                            <tr v-for="(item, idx) in explorerItems" :key="idx">
                                <td @click="item.is_dir ? fetchExplorer(item.path) : null" :style="item.is_dir ? 'cursor:pointer' : ''">
                                    <div class="d-flex align-items-center gap-2">
                                        <span>{{ item.is_dir ? '📁' : '📄' }}</span>
                                        <span :class="{'fw-bold': item.is_dir}">{{ item.name }}</span>
                                    </div>
                                </td>
                                <td class="text-muted small">
                                    {{ item.is_dir ? '-' : (item.size / 1024 / 1024).toFixed(2) + ' MB' }}
                                </td>
                                <td>
                                    <button v-if="!item.is_dir" class="btn btn-sm btn-outline-primary"
                                        @click="indexExploredFile(item)">Індексувати</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
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
            collections: [],
            activeCollectionId: null,
            localFilePath: '',
            explorerPath: '',
            explorerItems: []
        }
    },
    mounted() {
        this.fetchExplorer();
        this.fetchCollections();
    },
    methods: {
        async fetchCollections() {
            try {
                const res = await fetch('/api/media/collections/', { headers: this.auth() });
                const data = await res.json();
                this.collections = data.results || data;
            } catch (e) { }
        },
        async uploadFiles(e) {
            const files = e.target.files;
            if (!files.length) return;
            const formData = new FormData();
            for (let f of files) formData.append('files', f);
            if (this.activeCollectionId) formData.append('collection', this.activeCollectionId);

            try {
                const res = await fetch('/api/media/files/bulk-upload/', {
                    method: 'POST',
                    headers: this.auth(),
                    body: formData
                });
                if (res.ok) {
                    alert('Файли успішно завантажено!');
                    e.target.value = '';
                } else alert('Помилка завантаження.');
            } catch (e) { }
        },
        async indexLocalFile() {
            if (!this.localFilePath) return;
            try {
                const res = await fetch('/api/media/files/index-local/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', ...this.auth() },
                    body: JSON.stringify({
                        file_path: this.localFilePath,
                        visibility: 'public',
                        collection: this.activeCollectionId || null
                    })
                });
                if (res.ok) {
                    this.localFilePath = '';
                    alert('Файл успішно індексовано!');
                } else {
                    const error = await res.json();
                    let msg = 'Помилка: ' + (error.error || res.statusText);
                    alert(msg);
                }
            } catch (e) {
                alert('Помилка мережі при спробі індексації.');
            }
        },
        async fetchExplorer(path = '') {
            try {
                let url = '/api/media/explorer/';
                if (path) url += `?path=${encodeURIComponent(path)}`;
                const res = await fetch(url, { headers: this.auth() });
                const data = await res.json();
                if (res.ok) {
                    this.explorerPath = data.current_path;
                    this.explorerItems = data.items;
                }
            } catch (e) { }
        },
        async indexExploredFile(item) {
            try {
                const res = await fetch('/api/media/files/index-local/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', ...this.auth() },
                    body: JSON.stringify({
                        file_path: item.path,
                        visibility: 'public',
                        collection: this.activeCollectionId || null
                    })
                });
                if (res.ok) {
                    alert(`Файл "${item.name}" успішно індексовано!`);
                } else {
                    alert('Помилка індексації.');
                }
            } catch (e) {
                alert('Помилка мережі.');
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
</style>
