<template>
    <div class="eme-app-page">
        <div class="eme-app-header">
            <h1 class="eme-app-title">Налаштування</h1>
            <button class="btn btn-sm btn-ghost-secondary" @click="$emit('close')">✕</button>
        </div>

        <!-- Settings tabs -->
        <ul class="nav nav-tabs mb-4">
            <li class="nav-item">
                <a class="nav-link" :class="{active: settingsTab==='profile'}" href="#"
                    @click.prevent="settingsTab='profile'">👤 Профіль</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" :class="{active: settingsTab==='system'}" href="#"
                    @click.prevent="settingsTab='system'">🖥 Система</a>
            </li>
        </ul>

        <!-- Profile tab -->
        <div v-if="settingsTab === 'profile'">
            <div class="card">
                <div class="card-body">
                    <div class="row g-3 mb-3">
                        <div class="col-md-6">
                            <label class="form-label">Ім'я</label>
                            <input type="text" class="form-control" v-model="user.first_name">
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Локація</label>
                            <input type="text" class="form-control" v-model="user.address">
                        </div>
                        <div class="col-12">
                            <label class="form-label">Про мене</label>
                            <textarea class="form-control" v-model="user.bio" rows="3"></textarea>
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">Дата народження</label>
                            <input type="date" class="form-control" v-model="user.birth_date">
                        </div>
                    </div>

                    <!-- Social links -->
                    <label class="form-label">Соцмережі</label>
                    <div v-for="(s, i) in user.social_links" :key="s.id"
                        class="d-flex align-items-center gap-2 mb-2 p-2 rounded"
                        style="background:rgba(255,255,255,.03);border:1px solid var(--tblr-border-color);">
                        <span class="fw-bold" style="min-width:80px;">{{ s.network_name }}</span>
                        <span class="text-muted flex-grow-1">{{ s.link }}</span>
                        <button class="btn btn-ghost-danger btn-sm btn-icon"
                            @click="deleteSocial(s.id, i)">✕</button>
                    </div>
                    <div class="row g-2 mt-1">
                        <div class="col-3">
                            <input type="text" class="form-control form-control-sm" v-model="newSocial.name"
                                placeholder="Telegram">
                        </div>
                        <div class="col-7">
                            <input type="text" class="form-control form-control-sm" v-model="newSocial.link"
                                placeholder="@username">
                        </div>
                        <div class="col-2">
                            <button class="btn btn-sm btn-outline-secondary w-100" @click="addSocial">+ Додати</button>
                        </div>
                    </div>

                    <div class="mt-4">
                        <button class="btn btn-primary" @click="saveProfile" :disabled="loading">
                            <span v-if="loading" class="spinner-border spinner-border-sm me-1"></span>
                            Зберегти зміни
                        </button>
                        <span v-if="saveSuccess" class="ms-3 text-success">✅ Збережено!</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- System tab -->
        <div v-if="settingsTab === 'system'">
            <div class="card">
                <div class="card-body">
                    <div class="mb-3">
                        <label class="form-label">Назва Ноди</label>
                        <input type="text" class="form-control" v-model="localSettings.node_name"
                            style="max-width:320px;">
                    </div>
                    <div class="mb-4">
                        <label class="form-label">Тема оформлення</label>
                        <select class="form-select" v-model="localSettings.theme" style="max-width:220px;">
                            <option value="dark">Dark Cyber</option>
                            <option value="light">Light Mesh</option>
                        </select>
                    </div>
                    <button class="btn btn-primary" @click="saveSystemSettings" :disabled="loading">
                        <span v-if="loading" class="spinner-border spinner-border-sm me-1"></span>
                        Зберегти
                    </button>
                    <span v-if="saveSuccess" class="ms-3 text-success">✅ Збережено!</span>
                    <hr class="my-4">
                    <h3 class="card-title mb-3">Мобільне розгортання</h3>
                    <p class="text-muted small">Скануйте QR-код або скопіюйте команду нижче, щоб швидко розгорнути EME OS на вашому Android пристрої через Termux.</p>
                    
                    <div class="row align-items-center g-3">
                        <div class="col-auto">
                            <div class="p-2 bg-white rounded shadow-sm" style="width:160px;height:160px;">
                                <img :src="qrUrl" alt="Termux Setup QR" style="width:100%;height:100%;">
                            </div>
                        </div>
                        <div class="col">
                            <div class="input-group mb-2">
                                <input type="text" class="form-control form-control-sm bg-dark text-info font-monospace" readonly :value="termuxCommand">
                                <button class="btn btn-sm btn-outline-info" @click="copyCommand">Копіювати</button>
                            </div>
                            <ol class="small text-muted ps-3 mb-0">
                                <li>Відкрийте <b>Termux</b> на телефоні.</li>
                                <li>Вставте скопійовану команду (або скануйте QR за посиланням).</li>
                                <li>Натисніть <b>Enter</b> та дочекайтеся завершення.</li>
                            </ol>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    props: ['user', 'systemSettings', 'auth'],
    data() {
        return {
            settingsTab: 'profile',
            loading: false,
            saveSuccess: false,
            newSocial: { name: '', link: '' },
            localSettings: { ...this.systemSettings },
            copySuccess: false
        }
    },
    watch: {
        systemSettings: {
            deep: true,
            handler(nv) {
                this.localSettings = { ...nv };
            }
        }
    },
    computed: {
        termuxCommand() {
            const ip = this.localSettings.server_ip || '127.0.0.1';
            return `curl -L http://${ip}:8080/bootstrap_eme.sh | bash -s -- ${ip}`;
        },
        qrUrl() {
            return `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(this.termuxCommand)}`;
        }
    },
    methods: {
        async saveProfile() {
            this.loading = true;
            try {
                const res = await fetch('/api/profiles/me/', {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json', ...this.auth() },
                    body: JSON.stringify(this.user)
                });
                if (res.ok) {
                    this.saveSuccess = true;
                    setTimeout(() => this.saveSuccess = false, 1500);
                    this.$emit('update:user', await res.json());
                }
            } catch (e) { } finally { this.loading = false; }
        },
        async addSocial() {
            if (!this.newSocial.name || !this.newSocial.link) return;
            try {
                const res = await fetch('/api/profiles/social-links/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', ...this.auth() },
                    body: JSON.stringify({
                        network_name: this.newSocial.name,
                        link: this.newSocial.link
                    })
                });
                if (res.ok) {
                    this.newSocial = { name: '', link: '' };
                    this.$emit('refresh-user');
                }
            } catch (e) { }
        },
        async deleteSocial(id) {
            try {
                const res = await fetch(`/api/profiles/social-links/${id}/`, {
                    method: 'DELETE',
                    headers: this.auth()
                });
                if (res.ok) this.$emit('refresh-user');
            } catch (e) { }
        },
        async saveSystemSettings() {
            this.loading = true;
            try {
                const res = await fetch('/api/settings/me/', {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json', ...this.auth() },
                    body: JSON.stringify(this.localSettings)
                });
                if (res.ok) {
                    this.saveSuccess = true;
                    setTimeout(() => this.saveSuccess = false, 1500);
                    this.$emit('update:system-settings', await res.json());
                }
            } catch (e) { } finally { this.loading = false; }
        },
        copyCommand() {
            navigator.clipboard.writeText(this.termuxCommand);
            alert('Команду скопійовано у буфер обміну!');
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
</style>
