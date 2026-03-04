<template>
    <div class="eme-auth-wrapper">
        <!-- SCREEN: AUTH -->
        <div v-if="localView === 'auth'" class="eme-auth-screen">
            <div class="eme-auth-logo">
                <div class="eme-logo-mark">E</div>
                <div>
                    <span class="grad-text" style="font-size:1.8rem;font-weight:900;letter-spacing:-1px;">EME OS</span>
                </div>
                <p class="text-muted mt-1" style="font-size:12px;">Децентралізована Соціальна ОС</p>
            </div>

            <div class="card" style="width:100%;max-width:420px;">
                <div class="card-body">
                    <!-- Tab switcher -->
                    <div class="eme-auth-tabs">
                        <button class="eme-auth-tab" :class="{active: !isLogin}" @click="switchMode(false)">
                            Реєстрація
                        </button>
                        <button class="eme-auth-tab" :class="{active: isLogin}" @click="switchMode(true)">
                            Вхід
                        </button>
                    </div>

                    <!-- Username -->
                    <div class="mb-3">
                        <label class="form-label">Логін</label>
                        <input type="text" class="form-control" v-model="form.username"
                            :placeholder="isLogin ? 'Ваш логін' : 'Оберіть логін'" autocomplete="username"
                            @keyup.enter="submit">
                    </div>

                    <!-- First name - register only -->
                    <div class="mb-3" v-show="!isLogin">
                        <label class="form-label">Ім'я</label>
                        <input type="text" class="form-control" v-model="form.first_name" placeholder="Як вас звати?"
                            autocomplete="given-name">
                    </div>

                    <!-- Password -->
                    <div class="mb-3">
                        <label class="form-label">Пароль</label>
                        <input type="password" class="form-control" v-model="form.password" placeholder="••••••••"
                            autocomplete="current-password" @keyup.enter="submit">
                    </div>

                    <!-- Submit -->
                    <div class="d-grid">
                        <button class="btn btn-primary" @click="submit" :disabled="loading">
                            <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
                            {{ isLogin ? 'Увійти' : 'Створити акаунт' }}
                        </button>
                    </div>

                    <!-- Error -->
                    <div v-if="error" class="alert alert-danger mt-3 py-2 mb-0" style="font-size:13px;">
                        {{ error }}
                    </div>
                </div>
            </div>
        </div>

        <!-- SCREEN: FIRST-RUN SETUP -->
        <div v-if="localView === 'setup'" class="eme-auth-screen">
            <div class="eme-auth-logo">
                <div class="eme-logo-mark">E</div>
                <span class="grad-text" style="font-size:1.5rem;font-weight:900;">Розкажи про себе</span>
                <p class="text-muted mt-1" style="font-size:12px;">Заповни профіль щоб продовжити</p>
            </div>

            <div class="card" style="width:100%;max-width:480px;">
                <div class="card-body">
                    <div class="mb-3">
                        <label class="form-label">Про мене (Bio)</label>
                        <textarea class="form-control" v-model="user.bio" placeholder="Що ви робите в EME?"
                            rows="3"></textarea>
                    </div>
                    <div class="row g-3 mb-3">
                        <div class="col-6">
                            <label class="form-label">Дата народження</label>
                            <input type="date" class="form-control" v-model="user.birth_date">
                        </div>
                        <div class="col-6">
                            <label class="form-label">Місто / Країна</label>
                            <input type="text" class="form-control" v-model="user.address" placeholder="Київ, Україна">
                        </div>
                    </div>
                    <div class="d-grid">
                        <button class="btn btn-primary" @click="saveProfile" :disabled="loading">
                            <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
                            Зайти в систему →
                        </button>
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
            localView: 'auth',
            isLogin: true,
            loading: false,
            error: null,
            form: {
                username: '',
                password: '',
                first_name: ''
            }
        }
    },
    methods: {
        switchMode(isLogin) {
            this.isLogin = isLogin;
            this.error = null;
        },
        async submit() {
            this.loading = true;
            this.error = null;
            const url = this.isLogin ? '/api/profiles/login/' : '/api/profiles/register/';
            try {
                const res = await fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(this.form)
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || data.username || 'Помилка авторизації');

                if (data.access) {
                    localStorage.setItem('access_token', data.access);
                    localStorage.setItem('refresh_token', data.refresh);
                } else {
                    throw new Error('Invalid token response');
                }

                // Call parent to load data
                this.$emit('authenticated');
                
                if (!data.bio && !this.isLogin) {
                    this.localView = 'setup';
                } else {
                    this.$emit('success');
                }
            } catch (e) {
                this.error = e.message;
            } finally {
                this.loading = false;
            }
        },
        async saveProfile() {
            this.loading = true;
            try {
                const res = await fetch('/api/profiles/me/', {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json', ...this.auth() },
                    body: JSON.stringify(this.user)
                });
                if (res.ok) {
                    const updatedUser = await res.json();
                    this.$emit('update:user', updatedUser);
                    this.$emit('success');
                }
            } catch (e) {
            } finally {
                this.loading = false;
            }
        }
    }
}
</script>

<style scoped>
.eme-auth-screen {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 28px;
    padding: 24px;
    background: var(--tblr-body-bg);
}

.eme-auth-logo {
    text-align: center;
}

.eme-logo-mark {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 54px;
    height: 54px;
    border-radius: 14px;
    background: var(--eme-grad);
    font-size: 1.7rem;
    font-weight: 900;
    color: white;
    margin-bottom: 10px;
    box-shadow: 0 8px 24px rgba(0, 229, 255, .25);
}

.eme-auth-tabs {
    display: flex;
    gap: 4px;
    background: rgba(255, 255, 255, .05);
    border: 1px solid var(--tblr-border-color);
    border-radius: 10px;
    padding: 4px;
    margin-bottom: 20px;
}

.eme-auth-tab {
    flex: 1;
    padding: 9px;
    background: transparent;
    border: none;
    border-radius: 7px;
    color: var(--tblr-secondary);
    font-size: 13.5px;
    font-weight: 600;
    cursor: pointer;
    transition: .18s;
    font-family: inherit;
}

.eme-auth-tab.active {
    background: var(--tblr-card-bg);
    color: var(--tblr-body-color);
    box-shadow: 0 2px 8px rgba(0, 0, 0, .3);
}

.grad-text {
    background: var(--eme-grad);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
}
</style>
