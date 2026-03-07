<template>
    <div class="eme-app-page">
        <!-- Visiting User Banner -->
        <div v-if="visitingUser && visitingUser.id !== user.id" class="alert alert-info bg-primary-lt border-primary mb-3 py-2">
            <div class="d-flex align-items-center justify-content-between">
                <div>
                    <strong>👤 Перегляд чужого профілю:</strong> {{ visitingUser.username }}
                </div>
                <button class="btn btn-sm btn-primary" @click="$emit('return')">Повернутись до себе</button>
            </div>
        </div>

        <div class="eme-app-header">
            <div class="d-flex align-items-center gap-3">
                <h1 class="eme-app-title">Профіль</h1>
            </div>
            <button class="btn btn-sm btn-ghost-secondary" @click="$emit('close')">✕</button>
        </div>

        <div class="row g-4">
            <!-- Left Column: Avatar & Quick Stats -->
            <div class="col-md-4 col-lg-3">
                <div class="card text-center p-4">
                    <div class="avatar-wrapper mb-3 position-relative mx-auto" style="width: 150px; height: 150px;">
                        <img v-if="displayUser.avatar" :src="displayUser.avatar" class="rounded-circle w-100 h-100 object-fit-cover shadow-sm">
                        <div v-else class="rounded-circle w-100 h-100 bg-primary-lt d-flex align-items-center justify-content-center display-1 text-primary shadow-sm">
                            {{ (displayUser.username || '?').charAt(0).toUpperCase() }}
                        </div>
                        
                        <!-- Avatar Upload (Only for own profile) -->
                        <div v-if="isOwnProfile" class="avatar-upload-overlay">
                            <label class="btn btn-icon btn-primary rounded-circle shadow" title="Завантажити нове фото">
                                📷
                                <input type="file" class="d-none" accept="image/*" @change="uploadAvatar">
                            </label>
                        </div>
                    </div>

                    <h3 class="mb-1">{{ displayUser.first_name }} {{ displayUser.last_name }}</h3>
                    <div class="text-muted mb-3">@{{ displayUser.username }}</div>
                    
                    <div class="d-flex justify-content-center gap-2 mb-3">
                        <span class="badge bg-green-lt" title="Рівень">⭐ Рівень {{ displayUser.level || 1 }}</span>
                        <span class="badge bg-blue-lt" title="Бали">🪙 {{ displayUser.points || 0 }} EME</span>
                    </div>

                    <div v-if="!isOwnProfile" class="d-grid mt-3">
                        <button class="btn" :class="displayUser.is_followed ? 'btn-secondary' : 'btn-primary'" @click="toggleFollow" :disabled="loadingFollow">
                            {{ displayUser.is_followed ? 'Відписатися' : 'Підписатися' }}
                        </button>
                    </div>
                </div>
            </div>

            <!-- Right Column: Details & Social -->
            <div class="col-md-8 col-lg-9">
                <div class="card mb-4">
                    <div class="card-header">
                        <h4 class="card-title m-0">Про себе</h4>
                    </div>
                    <div class="card-body">
                        <p v-if="displayUser.bio" style="white-space: pre-wrap;">{{ displayUser.bio }}</p>
                        <p v-else class="text-muted fst-italic">Інформація відсутня.</p>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <h4 class="card-title m-0">Соціальні мережі</h4>
                    </div>
                    <div class="card-body">
                        <div v-if="displayUser.social_links && displayUser.social_links.length > 0" class="d-flex flex-wrap gap-2">
                            <a v-for="link in displayUser.social_links" :key="link.id" :href="link.link" target="_blank" class="btn btn-outline-secondary">
                                🔗 {{ link.name }}
                            </a>
                        </div>
                        <p v-else class="text-muted fst-italic m-0">Немає закріплених посилань.</p>
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
            loadingFollow: false
        }
    },
    computed: {
        displayUser() {
            return this.visitingUser || this.user || {};
        },
        isOwnProfile() {
            return !this.visitingUser || this.visitingUser.id === this.user.id;
        }
    },
    methods: {
        async uploadAvatar(event) {
            const file = event.target.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append('avatar', file);

            try {
                const res = await fetch('/api/profiles/me/avatar/', {
                    method: 'PATCH',
                    headers: { 'Authorization': this.auth().Authorization },
                    body: formData
                });
                if (res.ok) {
                    const data = await res.json();
                    this.$emit('update-user-avatar', data.avatar);
                    this.$emit('refresh-user');
                    // Reset input
                    event.target.value = '';
                } else {
                    alert('Помилка завантаження аватару.');
                }
            } catch (e) {
                console.error(e);
                alert('Сталася помилка.');
            }
        },
        async toggleFollow() {
            if (!this.visitingUser) return;
            this.loadingFollow = true;
            try {
                const method = this.displayUser.is_followed ? 'DELETE' : 'POST';
                const action = this.displayUser.is_followed ? 'unfollow' : 'follow';
                const res = await fetch(`/api/profiles/users/${this.displayUser.id}/${action}/`, {
                    method: method,
                    headers: this.auth()
                });
                
                if (res.ok) {
                    // Update locally
                    this.visitingUser.is_followed = !this.visitingUser.is_followed;
                }
            } catch (e) {
                console.error(e);
            }
            this.loadingFollow = false;
        }
    }
}
</script>

<style scoped>
.avatar-wrapper:hover .avatar-upload-overlay {
    opacity: 1;
}

.avatar-upload-overlay {
    position: absolute;
    bottom: 0;
    right: 0;
    opacity: 0;
    transition: opacity 0.2s ease;
}

.avatar-upload-overlay .btn {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    cursor: pointer;
}
</style>
