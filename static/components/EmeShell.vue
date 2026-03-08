<template>
    <div class="eme-shell">
        <!-- COLUMN 1: NAV STRIP (GLASS) -->
        <div class="eme-nav-col">
            <nav class="eme-nav">
                <div class="eme-nav-logo">
                    <div class="logo-inner">E</div>
                </div>

                <div class="nav-items-wrapper">
                    <button v-for="item in structuredNav" :key="item.item_id" class="eme-nav-btn"
                        :class="{ 'active': isActive(item) }" 
                        @click="handleAppClick(item)"
                        :title="item.label">
                        <div class="btn-indicator"></div>
                        <span class="nav-icon" style="font-size: 1.6rem;">{{ item.icon }}</span>
                        <span class="nav-label">{{ (item.label || '') }}</span>
                    </button>
                </div>

                <div class="mt-auto pb-4">
                    <button class="eme-nav-btn logout-btn" title="Вийти" @click="$emit('logout')">
                        <span class="nav-icon">🚪</span>
                        <span class="nav-label">Вийти</span>
                    </button>
                </div>
            </nav>
        </div>

        <!-- COLUMN 3: MAIN CONTENT AREA -->
        <div class="eme-main-col" :class="{'no-padding': isFullscreenApp}">
            <!-- Dynamic Content Slot -->
            <transition name="page" mode="out-in">
                <div :key="activeApp || 'empty'" class="page-wrapper">
                    <slot></slot>
                </div>
            </transition>
        </div>
    </div>
</template>

<script>
export default {
    props: ['navItems', 'activeApp', 'systemSettings', 'customApps'],
    computed: {
        isFullscreenApp() {
            const full = ['kb', 'projects', 'chat', 'clone_master', 'park_adventures', 'mafia'];
            return full.includes(this.activeApp);
        },
        structuredNav() {
            const core = [
                { item_id: 'desktop', label: 'Домашня', icon: '🏠' },
                { item_id: 'apps_store', label: 'Маркет', icon: '🛍️' },
                { item_id: 'settings', label: 'Налашт.', icon: '⚙️' }
            ];
            
            const dockApps = (this.systemSettings && this.systemSettings.dock_apps) || [];
            
            // Map custom apps
            const apps = (this.customApps || []).map(app => ({
                item_id: 'custom_app_' + app.id,
                label: app.name,
                icon: app.icon || '📱',
                isCustomApp: true,
                appData: app,
                order: app.order || 0
            }));

            let combined = [...core, ...apps];
            
            if (dockApps.length > 0) {
                // If customized, show ONLY what is in dockApps, in that order
                combined = combined.filter(c => dockApps.includes(c.item_id));
                combined.sort((a, b) => dockApps.indexOf(a.item_id) - dockApps.indexOf(b.item_id));
            } else {
                // Default: sort by .order
                combined.sort((a, b) => (a.order || 0) - (b.order || 0));
            }

            return combined;
        }
    },
    methods: {
        openApp(appId) {
            this.$emit('update:activeApp', appId);
        },
        isActive(item) {
            if (this.activeApp && typeof this.activeApp === 'object') {
                if (item.isCustomApp && item.appData) {
                    return this.activeApp.id === item.appData.id;
                }
                return false;
            }
            if (!this.activeApp && item.item_id === 'desktop') return true;
            return this.activeApp === item.item_id;
        },
        handleAppClick(item) {
            if (item.isCustomApp && item.appData) {
                const customAppObj = Object.assign({ type: 'custom_app' }, item.appData);
                this.openApp(customAppObj);
            } else if (item.item_id === 'desktop') {
                this.openApp(null);
            } else {
                this.openApp(item.item_id);
            }
        }
    }
}
</script>

<style scoped>
.eme-shell {
    display: grid;
    grid-template-columns: 90px 1fr;
    height: 100vh;
    background: #0d0e1a;
    color: #e1e1e1;
    overflow: hidden;
}

.eme-nav-col {
    position: relative;
    z-index: 1000;
}

.eme-nav {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 20px 0;
    width: 90px;
    height: 100vh;
    background: rgba(26, 28, 46, 0.4);
    backdrop-filter: blur(25px);
    -webkit-backdrop-filter: blur(25px);
    border-right: 1px solid rgba(255, 255, 255, 0.05);
    box-shadow: 10px 0 30px rgba(0, 0, 0, 0.2);
    overflow-y: auto;
    overflow-x: hidden;
}

.eme-nav::-webkit-scrollbar {
    width: 0px;
}

.eme-nav-logo {
    width: 44px;
    height: 44px;
    padding: 2px;
    background: var(--eme-grad);
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 24px;
    flex-shrink: 0;
    box-shadow: 0 4px 15px rgba(0, 229, 255, 0.3);
}

.logo-inner {
    width: 100%;
    height: 100%;
    background: #0d0e1a;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 900;
    color: white;
    font-size: 1.4rem;
}

.nav-groups-wrapper {
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.nav-group {
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 100%;
}

.nav-group-title {
    font-size: 9px;
    font-weight: 800;
    color: rgba(255, 255, 255, 0.2);
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin-bottom: 8px;
    width: 100%;
    text-align: center;
}

.eme-nav-btn {
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 60px;
    height: 60px;
    background: transparent;
    border: none;
    border-radius: 12px;
    cursor: pointer;
    color: rgba(255, 255, 255, 0.4);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    margin-bottom: 4px;
    outline: none;
}

.btn-indicator {
    position: absolute;
    left: -12px;
    width: 4px;
    height: 0;
    background: var(--eme-accent);
    border-radius: 0 4px 4px 0;
    transition: all 0.3s ease;
    box-shadow: 0 0 10px var(--eme-accent);
}

.eme-nav-btn:hover {
    background: rgba(255, 255, 255, 0.05);
    color: white;
}

.eme-nav-btn.active {
    background: rgba(0, 229, 255, 0.1);
    color: var(--eme-accent);
}

.eme-nav-btn.active .btn-indicator {
    height: 24px;
    left: 0;
}

.nav-icon {
    font-size: 1.4rem;
    margin-bottom: 2px;
}

.nav-label {
    font-size: 10px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    opacity: 0.9;
    margin-top: 4px;
    text-align: center;
    line-height: 1;
}

.logout-btn {
    opacity: 0.6;
}

.logout-btn:hover {
    color: #ff4b4b;
    background: rgba(255, 75, 75, 0.1);
}

.eme-main-col {
    position: relative;
    padding: 30px;
    overflow-y: auto;
    background: radial-gradient(circle at top right, rgba(108, 0, 255, 0.05), transparent 400px),
                radial-gradient(circle at bottom left, rgba(0, 229, 255, 0.03), transparent 400px);
}

.eme-main-col.no-padding {
    padding: 0;
}

.page-wrapper {
    width: 100%;
    height: 100%;
}

/* Transitions */
.page-enter-active, .page-leave-active {
    transition: all 0.4s ease;
}
.page-enter-from {
    opacity: 0;
    transform: translateY(10px);
}
.page-leave-to {
    opacity: 0;
    transform: translateY(-10px);
}

.fade-enter-active, .fade-leave-active {
    transition: opacity 0.5s ease;
}
.fade-enter-from, .fade-leave-to {
    opacity: 0;
}

/* Empty State */
.eme-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 80vh;
}

.big-logo {
    font-size: 8rem;
    font-weight: 950;
    background: linear-gradient(180deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0) 100%);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -8px;
}

.status-dot {
    width: 8px;
    height: 8px;
    background: #00ff88;
    border-radius: 50%;
    margin-top: 20px;
    box-shadow: 0 0 15px #00ff88;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.5); opacity: 0.5; }
    100% { transform: scale(1); opacity: 1; }
}

@media (max-width: 768px) {
    .eme-shell {
        grid-template-columns: 1fr;
    }
    .eme-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        height: auto;
        flex-direction: row;
        justify-content: space-around;
        padding: 5px 10px;
        border-right: none;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        z-index: 2000;
        background: rgba(26, 28, 46, 0.95);
        overflow: visible;
    }
    .nav-groups-wrapper {
        flex-direction: row;
        gap: 0;
        justify-content: space-around;
    }
    .nav-group-title, .eme-nav-logo, .nav-label, .btn-indicator {
        display: none;
    }
    .eme-nav-btn {
        width: 50px;
        height: 50px;
        margin-bottom: 0;
    }
    .eme-main-col {
        padding: 15px;
        padding-bottom: 90px;
    }
    .mt-auto {
        margin-top: 0 !important;
    }
}
</style>
