<template>
    <div class="eme-shell">
        <!-- COLUMN 1: NAV STRIP -->
        <div class="eme-nav-col">
            <nav class="eme-nav">
                <div class="eme-nav-logo">E</div>

                <button v-for="item in navItems" :key="item.item_id" class="eme-nav-btn"
                    :class="{active: activeApp === item.item_id}" :title="item.label"
                    @click="openApp(item.item_id)">
                    <span class="nav-icon">{{ item.icon }}</span>
                    <span class="nav-label">{{ item.label }}</span>
                </button>

                <div class="mt-auto pb-3">
                    <button class="eme-nav-btn" title="Вийти" @click="$emit('logout')"
                        style="border-top: 1px solid var(--tblr-border-color); padding-top: 15px;">
                        <span class="nav-icon">🚪</span>
                        <span class="nav-label">Вийти</span>
                    </button>
                </div>
            </nav>
        </div>

        <!-- COLUMN 3: MAIN CONTENT AREA -->
        <div class="eme-main-col" :class="{'p-0': activeApp === 'kb' || activeApp === 'projects' || activeApp === 'chat' || activeApp === 'clone_master'}">
            <!-- Empty desktop -->
            <div v-if="!activeApp" class="eme-empty">
                <div class="big-logo">EME</div>
                <p class="mt-3 text-muted">Оберіть розділ у навігації ліворуч</p>
            </div>

            <!-- Dynamic Content Slot / Components -->
            <slot></slot>
        </div>
    </div>
</template>

<script>
export default {
    props: ['navItems', 'activeApp'],
    methods: {
        openApp(appId) {
            this.$emit('update:activeApp', appId);
        }
    }
}
</script>

<style scoped>
.eme-shell {
    display: grid;
    grid-template-columns: 72px 1fr;
    height: 100vh;
    overflow: hidden;
    box-sizing: border-box;
}

.eme-nav-col {
    background: var(--tblr-dark, #1a1c2e);
}

.eme-nav {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 14px 0 12px;
    gap: 2px;
    width: 72px;
    border-right: 1px solid var(--tblr-border-color);
    min-height: 100vh;
    position: fixed;
    left: 0;
    top: 0;
    background: var(--tblr-navbar-bg, #1a1c2e);
    z-index: 100;
}

.eme-nav-logo {
    width: 38px;
    height: 38px;
    border-radius: 10px;
    background: var(--eme-grad);
    color: white;
    font-weight: 900;
    font-size: 1.2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 14px;
    flex-shrink: 0;
}

.eme-nav-btn {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 3px;
    width: 56px;
    padding: 9px 4px;
    background: transparent;
    border: 1px solid transparent;
    border-radius: 10px;
    cursor: pointer;
    font-family: inherit;
    color: var(--tblr-secondary);
    transition: .16s;
    margin-bottom: 2px;
}

.eme-nav-btn .nav-icon {
    font-size: 1.3rem;
    line-height: 1;
}

.eme-nav-btn .nav-label {
    font-size: 7px;
    font-weight: 600;
    letter-spacing: .3px;
    text-align: center;
    line-height: 1.4;
}

.eme-nav-btn:hover {
    background: rgba(255, 255, 255, .06);
    color: white;
}

.eme-nav-btn.active {
    background: rgba(0, 229, 255, .1);
    color: var(--eme-accent);
    border-color: rgba(0, 229, 255, .2);
}

.eme-main-col {
    padding: 24px;
    height: 100vh;
    overflow-y: auto !important;
    overflow-x: hidden;
    box-sizing: border-box;
}

/* MOBILE OPTIMIZATIONS */
@media (max-width: 768px) {
    .eme-shell {
        grid-template-columns: 1fr;
        padding-bottom: 70px; /* Space for fixed nav */
    }

    .eme-nav {
        width: 100%;
        height: 60px;
        min-height: auto;
        flex-direction: row;
        bottom: 0;
        top: auto;
        left: 0;
        right: 0;
        border-right: none;
        border-top: 1px solid var(--tblr-border-color);
        justify-content: space-around;
        padding: 0 10px;
        background: rgba(26, 28, 46, 0.95);
        backdrop-filter: blur(10px);
    }

    .eme-nav-logo {
        display: none; /* Hide logo on mobile nav strip */
    }

    .eme-nav-btn {
        width: auto;
        flex: 1;
        padding: 5px;
        margin-bottom: 0;
    }

    .eme-nav-btn .nav-icon {
        font-size: 1.5rem;
    }

    .eme-nav-btn .nav-label {
        display: none; /* Icons only on mobile */
    }

    .eme-main-col {
        padding: 12px;
    }

    .mt-auto {
        margin-top: 0 !important;
        padding-bottom: 0 !important;
    }

    .eme-nav-btn[title="Вийти"] {
        border-top: none !important;
        padding-top: 5px !important;
    }
}

.eme-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 60vh;
    color: var(--tblr-secondary);
}

.eme-empty .big-logo {
    font-size: 7rem;
    font-weight: 900;
    opacity: .06;
    letter-spacing: -8px;
    user-select: none;
    background: var(--eme-grad);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
}
</style>
