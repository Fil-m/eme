<template>
    <div :class="isWidget ? 'sysmon-widget' : 'eme-scroll-container'">
        <div :class="isWidget ? 'h-100 d-flex flex-column' : 'container-fluid py-4 min-vh-100'">
            
            <header v-if="!isWidget" class="mb-4 d-flex justify-content-between align-items-center">
                <div class="d-flex align-items-center gap-3">
                    <div class="header-icon-box">📈</div>
                    <div>
                        <h1 class="page-title m-0">Системний Монітор</h1>
                        <p class="text-muted m-0">Моніторинг ресурсів сервера EME OS</p>
                    </div>
                </div>
                <button class="btn btn-outline-info" @click="fetchStats">🔄 Оновити</button>
            </header>

            <!-- Loading State -->
            <div v-if="loading && !stats" class="text-center py-4">
                <div class="spinner-border text-info mb-2" role="status"></div>
                <div class="text-muted small">Отримання даних...</div>
            </div>
            
            <!-- Error State -->
            <div v-else-if="error" class="alert alert-danger">
                {{ error }}
            </div>

            <!-- Dashboard / Full View Grid -->
            <div v-else class="row g-3" :class="isWidget ? 'flex-grow-1' : ''">
                <!-- CPU -->
                <div :class="isWidget ? 'col-6' : 'col-md-4'">
                    <div class="metric-card bg-dark border-secondary p-3 h-100 rounded">
                        <div class="d-flex justify-content-between mb-2">
                            <span class="text-white fw-bold">CPU</span>
                            <span class="text-info">{{ stats.cpu }}%</span>
                        </div>
                        <div class="progress progress-sm bg-black">
                            <div class="progress-bar bg-info" :style="{ width: stats.cpu + '%' }"></div>
                        </div>
                        <div class="mt-2 text-muted small" v-if="!isWidget">Ядер: {{ stats.cpu_cores }}</div>
                    </div>
                </div>

                <!-- RAM -->
                <div :class="isWidget ? 'col-6' : 'col-md-4'">
                    <div class="metric-card bg-dark border-secondary p-3 h-100 rounded">
                        <div class="d-flex justify-content-between mb-2">
                            <span class="text-white fw-bold">RAM</span>
                            <span class="text-warning">{{ stats.ram_percent }}%</span>
                        </div>
                        <div class="progress progress-sm bg-black">
                            <div class="progress-bar bg-warning" :style="{ width: stats.ram_percent + '%' }"></div>
                        </div>
                        <div class="mt-2 text-muted small" v-if="!isWidget">
                            {{ formatBytes(stats.ram_used) }} / {{ formatBytes(stats.ram_total) }}
                        </div>
                    </div>
                </div>

                <!-- Disk -->
                <div :class="isWidget ? 'col-12 mt-3' : 'col-md-4'">
                    <div class="metric-card bg-dark border-secondary p-3 h-100 rounded">
                        <div class="d-flex justify-content-between mb-2">
                            <span class="text-white fw-bold">Диск (OS)</span>
                            <span class="text-success">{{ stats.disk_percent }}%</span>
                        </div>
                        <div class="progress progress-sm bg-black">
                            <div class="progress-bar bg-success" :style="{ width: stats.disk_percent + '%' }"></div>
                        </div>
                        <div class="mt-2 text-muted small" v-if="!isWidget">
                            {{ formatBytes(stats.disk_used) }} / {{ formatBytes(stats.disk_total) }}
                        </div>
                    </div>
                </div>
                
                <!-- Uptime -->
                <div v-if="!isWidget" class="col-12 mt-4">
                    <div class="card bg-dark border-secondary p-4">
                        <h4 class="text-white mb-3">Деталі системи</h4>
                        <p class="text-muted m-0">Час запуску системи: <strong class="text-white">{{ new Date(stats.boot_time * 1000).toLocaleString('uk-UA') }}</strong></p>
                    </div>
                </div>
            </div>
            
            <div v-if="isWidget" class="mt-auto pt-3 text-end">
                <button class="btn btn-sm btn-ghost-info" @click="$emit('open-app', 'sysmon')">Детальніше ↗</button>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    props: {
        user: Object,
        auth: Function,
        isWidget: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            stats: null,
            loading: true,
            error: null,
            timer: null
        }
    },
    methods: {
        async fetchStats() {
            this.loading = true;
            try {
                const res = await fetch('/api/utils/sysmon/', { headers: this.auth() });
                if (res.ok) {
                    const data = await res.json();
                    if (data.error) throw new Error(data.error);
                    this.stats = data;
                    this.error = null;
                } else {
                    throw new Error('Server error');
                }
            } catch (e) {
                this.error = 'Не вдалося завантажити системні дані.';
            } finally {
                this.loading = false;
            }
        },
        formatBytes(bytes, decimals = 2) {
            if (!+bytes) return '0 Bytes';
            const k = 1024;
            const dm = decimals < 0 ? 0 : decimals;
            const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
        }
    },
    mounted() {
        this.fetchStats();
        // Update every 5 seconds
        this.timer = setInterval(this.fetchStats, 5000);
    },
    unmounted() {
        if(this.timer) clearInterval(this.timer);
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

.metric-card {
    transition: transform 0.2s, box-shadow 0.2s;
    border: 1px solid rgba(255,255,255,0.05) !important;
}

.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(0,0,0,0.3);
}

.sysmon-widget {
    height: 100%;
}
</style>
