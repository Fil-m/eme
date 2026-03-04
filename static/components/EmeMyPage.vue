<template>
    <div class="eme-app-page">
        <div v-if="visitingUser"
            class="alert alert-info alert-dismissible bg-primary-lt border-primary mb-3 py-2">
            <div class="d-flex align-items-center justify-content-between">
                <span>🌐 Ви переглядаєте профіль користувача <b>{{ visitingUser.username }}</b></span>
                <button class="btn btn-sm btn-primary" @click="$emit('return')">Повернутись до
                    себе</button>
            </div>
        </div>
        <div class="eme-app-header">
            <h1 class="eme-app-title">Моя сторінка</h1>
            <button class="btn btn-sm btn-ghost-secondary" @click="$emit('close')">✕</button>
        </div>

        <!-- Hero Card -->
        <div class="card mb-3">
            <div class="card-body">
                <div class="d-flex align-items-center gap-4">
                    <div class="eme-avatar"
                        style="width:100px;height:100px;font-size:2.5rem;flex-shrink:0;">
                        <img v-if="currentUser.avatar" :src="currentUser.avatar">
                        <span v-else>{{ (currentUser.first_name || currentUser.username || 'U')[0].toUpperCase() }}</span>
                    </div>
                    <div>
                        <h2 class="mb-1" style="font-size:1.6rem;font-weight:800;">{{ currentUser.first_name || currentUser.username }}</h2>
                        <div class="text-muted mb-2">@{{ currentUser.username }}</div>
                        <div class="eme-xp-badge">EME LVL {{ currentUser.level }} · {{ currentUser.points }} XP</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Info row -->
        <div class="row g-3 mb-3">
            <div class="col-md-8">
                <div class="card h-100">
                    <div class="card-header"><strong>Про мене</strong></div>
                    <div class="card-body">
                        <p v-if="currentUser.bio" class="mb-0">{{ currentUser.bio }}</p>
                        <p v-else class="text-muted mb-0">Bio не заповнено</p>
                        <p v-if="currentUser.address" class="mt-2 mb-0"><span class="me-1">📍</span>{{ currentUser.address }}</p>
                        <p v-if="currentUser.birth_date" class="mt-1 mb-0"><span class="me-1">🎂</span>{{ currentUser.birth_date }}</p>
                        <!-- Social links -->
                        <div v-if="currentUser.social_links && currentUser.social_links.length"
                            class="mt-2 d-flex flex-wrap gap-2">
                            <span v-for="s in currentUser.social_links" :key="s.id"
                                class="badge bg-blue-lt">{{ s.network_name }}: {{ s.link }}</span>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card h-100">
                    <div class="card-header"><strong>Активність</strong></div>
                    <div class="card-body">
                        <div class="d-flex align-items-center justify-content-between mb-2">
                            <span class="text-muted">Рівень</span>
                            <span class="fw-bold">{{ currentUser.level }}</span>
                        </div>
                        <div class="progress mb-2" style="height:6px;">
                            <div class="progress-bar bg-cyan"
                                :style="'width:' + (currentUser.points % 100) + '%'">
                            </div>
                        </div>
                        <div class="text-muted" style="font-size:11px;">{{ currentUser.points }} XP · до наступного: {{ 100 - (currentUser.points % 100) }} XP</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Wall / Feed (placeholder) -->
        <div class="card">
            <div class="card-header"><strong>📋 Стіна (Wall)</strong></div>
            <div class="card-body">
                <div class="module-placeholder">
                    <div style="font-size:2rem;">📝</div>
                    <div class="mt-2 fw-bold">Модуль Wall</div>
                    <div class="text-muted mt-1" style="font-size:12px;">Тут будуть пости та активність користувача</div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    props: ['user', 'visitingUser'],
    computed: {
        currentUser() {
            return this.visitingUser || this.user;
        }
    }
}
</script>

<style scoped>
.eme-avatar {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    border: 3px solid var(--eme-accent);
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2rem;
    font-weight: 800;
    background: var(--tblr-card-bg);
    margin: 0 auto 12px;
    color: var(--eme-accent);
}

.eme-avatar img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.eme-xp-badge {
    display: inline-block;
    padding: 3px 10px;
    background: rgba(0, 229, 255, .08);
    border: 1px solid rgba(0, 229, 255, .2);
    border-radius: 20px;
    font-size: 10px;
    color: var(--eme-accent);
}

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

.module-placeholder {
    background: var(--tblr-card-bg);
    border: 1px dashed var(--tblr-border-color);
    border-radius: 12px;
    padding: 32px;
    text-align: center;
    color: var(--tblr-secondary);
}
</style>
