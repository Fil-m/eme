<template>
    <div class="chat-shell d-flex" style="height:100vh;">

        <!-- ===== PANEL 1: ROOM LIST ===== -->
        <div class="chat-sidebar d-flex flex-column" :class="{collapsed: activeRoom && mobile}">
            <div class="chat-sidebar-header px-3 py-3 d-flex align-items-center justify-content-between">
                <span class="fw-bold" style="font-size:1.1rem; background:var(--eme-grad);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent">💬 Чат</span>
                <div class="d-flex gap-1">
                    <button class="btn btn-icon btn-xs btn-ghost-secondary" @click="showNewRoom=true" title="Нова кімната">➕</button>
                    <button class="btn btn-sm btn-ghost-secondary" @click="$emit('close')">✕</button>
                </div>
            </div>

            <div class="px-2 pb-2">
                <input class="form-control form-control-sm" placeholder="🔍 Пошук..." v-model="roomSearch">
            </div>

            <div class="flex-grow-1 overflow-auto">
                <!-- General rooms (always visible) -->
                <div class="room-section-label px-3 py-1">Загальні</div>
                <div v-for="r in generalRooms" :key="r.id" class="room-item" :class="{active: activeRoom && activeRoom.id === r.id}" @click="openRoom(r)">
                    <div class="room-avatar">🌐</div>
                    <div class="room-info">
                        <div class="room-name">{{ r.title }}</div>
                        <div class="room-preview" v-if="r.last_message">{{ r.last_message.sender }}: {{ r.last_message.text }}</div>
                    </div>
                </div>

                <!-- DMs -->
                <div class="room-section-label px-3 py-1 mt-2">Приватні</div>
                <div v-for="r in dmRooms" :key="r.id" class="room-item" :class="{active: activeRoom && activeRoom.id === r.id}" @click="openRoom(r)">
                    <div class="room-avatar">💬</div>
                    <div class="room-info">
                        <div class="room-name">{{ r.title || 'DM' }}</div>
                        <div class="room-preview" v-if="r.last_message">{{ r.last_message.text }}</div>
                    </div>
                </div>

                <!-- Group rooms -->
                <div class="room-section-label px-3 py-1 mt-2">Групи</div>
                <div v-for="r in groupRooms" :key="r.id" class="room-item" :class="{active: activeRoom && activeRoom.id === r.id}" @click="openRoom(r)">
                    <div class="room-avatar">👥</div>
                    <div class="room-info">
                        <div class="room-name">{{ r.title }}</div>
                        <div class="room-preview" v-if="r.last_message">{{ r.last_message.sender }}: {{ r.last_message.text }}</div>
                    </div>
                </div>

                <div v-if="!rooms.length && !loading" class="text-center text-muted py-5 small px-3">
                    Натисніть ➕ щоб criar першу групу або напишіть комусь з мережі
                </div>
            </div>

            <!-- Chat Settings button -->
            <div class="p-2 border-top-subtle">
                <button class="btn btn-ghost-secondary btn-sm w-100" @click="showSettings=true">⚙️ Налаштування чату</button>
            </div>
        </div>

        <!-- ===== PANEL 2: MESSAGES ===== -->
        <div class="chat-main d-flex flex-column flex-grow-1" v-if="activeRoom">
            <!-- Room Header -->
            <div class="chat-main-header px-4 py-3 d-flex align-items-center gap-3">
                <button class="btn btn-icon btn-xs btn-ghost-secondary" @click="activeRoom=null" v-if="mobile">←</button>
                <div class="room-avatar-lg">{{ activeRoom.kind === 'general' ? '🌐' : activeRoom.kind === 'dm' ? '💬' : '👥' }}</div>
                <div class="flex-grow-1">
                    <div class="fw-bold">{{ activeRoom.title || 'Чат' }}</div>
                    <div class="small text-muted">{{ activeRoom.members_count }} учасників</div>
                </div>
                <div class="d-flex gap-1">
                    <button class="btn btn-xs btn-ghost-secondary" @click="showInfo = !showInfo" title="Учасники">👥</button>
                </div>
            </div>

            <!-- Message Timeline -->
            <div class="chat-messages flex-grow-1 overflow-auto px-4 py-3" ref="msgList">
                <div v-if="msgsLoading" class="text-center py-4"><div class="spinner-border text-cyan spinner-border-sm"></div></div>

                <template v-for="msg in messages" :key="msg.id">
                    <div class="msg-row" :class="{'msg-row--mine': msg.sender === myUserId}">
                        <!-- Avatar for others -->
                        <div class="msg-avatar" v-if="msg.sender !== myUserId">
                            {{ (msg.sender_info?.username || '?')[0].toUpperCase() }}
                        </div>

                        <div class="msg-bubble-wrap">
                            <div class="msg-name small text-muted mb-1" v-if="msg.sender !== myUserId">
                                {{ msg.sender_info?.first_name || msg.sender_info?.username }}
                            </div>

                            <!-- TEXT message -->
                            <div v-if="msg.msg_type === 'text'" class="msg-bubble" :class="{'msg-bubble--mine': msg.sender === myUserId}">
                                {{ msg.text }}
                            </div>

                            <!-- STICKER message -->
                            <div v-else-if="msg.msg_type === 'sticker' || msg.msg_type === 'pixel'" class="msg-sticker">
                                <img :src="msg.sticker_data?.image_url" :alt="msg.sticker_data?.label" class="sticker-img">
                                <div class="sticker-label" v-if="msg.sticker_data?.label">{{ msg.sticker_data.label }}</div>
                            </div>

                            <!-- FILE message -->
                            <div v-else-if="msg.msg_type === 'file' || msg.msg_type === 'image'" class="msg-bubble msg-bubble--file" :class="{'msg-bubble--mine': msg.sender === myUserId}">
                                <a :href="msg.attachment_url" target="_blank" class="file-link">
                                    📎 {{ msg.attachment_name || 'Файл' }}
                                </a>
                                <div v-if="msg.msg_type === 'image'" class="mt-2">
                                    <img :src="msg.attachment_url" class="msg-image-preview" :alt="msg.attachment_name">
                                </div>
                            </div>

                            <div class="msg-time">{{ formatTime(msg.created_at) }}</div>
                        </div>
                    </div>
                </template>
            </div>

            <!-- Sticker Tray -->
            <transition name="slide-up">
                <div v-if="showStickerTray && chatSettings.stickers_enabled" class="sticker-tray px-3 py-2">
                    <div class="d-flex gap-2 mb-2">
                        <button v-for="pack in activePacks" :key="pack.id"
                            class="btn btn-xs" :class="activePack?.id === pack.id ? 'btn-primary' : 'btn-ghost-secondary'"
                            @click="activePack = pack">{{ pack.name }}</button>
                        <button class="btn btn-xs btn-ghost-secondary ms-auto" @click="showStickerTray=false">✕</button>
                    </div>
                    <div class="sticker-grid" v-if="activePack">
                        <div v-for="s in activePack.stickers" :key="s.id" class="sticker-cell" @click="sendSticker(s)" :title="s.label">
                            <img :src="s.image_url" :alt="s.label" class="sticker-thumb">
                            <div class="sticker-cell-label">{{ s.label }}</div>
                        </div>
                        <div v-if="!activePack.stickers.length" class="text-muted small ps-2">Стікерів немає</div>
                    </div>
                </div>
            </transition>

            <!-- Pixel Editor (opt-in) -->
            <transition name="slide-up">
                <div v-if="showPixelEditor && chatSettings.pixel_editor_enabled" class="pixel-editor-tray p-3">
                    <div class="d-flex align-items-center mb-2 gap-2">
                        <span class="fw-bold small">🎨 Піксель-редактор</span>
                        <button class="btn btn-xs btn-ghost-secondary ms-auto" @click="showPixelEditor=false">✕</button>
                    </div>
                    <div class="d-flex gap-3 align-items-start flex-wrap">
                        <canvas ref="pixelCanvas" width="160" height="160" class="pixel-canvas"
                            @mousedown="pixelPainting=true; drawPixel($event)"
                            @mousemove="pixelPainting && drawPixel($event)"
                            @mouseup="pixelPainting=false"
                            @touchstart.prevent="pixelPainting=true; drawPixelTouch($event)"
                            @touchmove.prevent="drawPixelTouch($event)"
                            @touchend="pixelPainting=false">
                        </canvas>
                        <div>
                            <div class="d-flex flex-wrap gap-1 mb-2" style="max-width: 140px;">
                                <div v-for="c in PALETTE" :key="c" class="color-cell"
                                    :class="{active: pixelColor === c}"
                                    :style="'background:'+c"
                                    @click="pixelColor = c">
                                </div>
                            </div>
                            <input class="form-control form-control-sm mb-2" v-model="pixelLabel" placeholder="Підпис (необов'язково)">
                            <button class="btn btn-sm btn-primary w-100" @click="sendPixelArt">📤 Надіслати</button>
                            <button class="btn btn-sm btn-ghost-secondary w-100 mt-1" @click="clearCanvas">🗑 Очистити</button>
                        </div>
                    </div>
                </div>
            </transition>

            <!-- Message Input -->
            <div class="chat-input-bar px-3 py-2 d-flex align-items-end gap-2">
                <div class="d-flex gap-1">
                    <!-- Sticker button -->
                    <button v-if="chatSettings.stickers_enabled" class="btn btn-icon btn-xs btn-ghost-secondary"
                        @click="showStickerTray=!showStickerTray; showPixelEditor=false" title="Стікери">😊</button>
                    <!-- Pixel editor button -->
                    <button v-if="chatSettings.pixel_editor_enabled" class="btn btn-icon btn-xs btn-ghost-secondary"
                        @click="showPixelEditor=!showPixelEditor; showStickerTray=false" title="Піксель-редактор">🎨</button>
                    <!-- File attach -->
                    <label class="btn btn-icon btn-xs btn-ghost-secondary" title="Прикріпити файл">
                        📎
                        <input type="file" class="d-none" ref="fileInput" @change="attachFile">
                    </label>
                </div>

                <textarea ref="msgInput" class="form-control chat-textarea" rows="1" placeholder="Написати повідомлення..."
                    v-model="newMsg"
                    @keydown.enter.exact.prevent="sendText"
                    @input="autoGrow">
                </textarea>

                <button class="btn btn-primary btn-sm" @click="sendText" :disabled="!newMsg.trim()">→</button>
            </div>
        </div>

        <!-- Empty state when no room selected -->
        <div v-else class="flex-grow-1 d-flex flex-column align-items-center justify-content-center text-muted">
            <div style="font-size:5rem;">💬</div>
            <div class="mt-3 fw-bold">Оберіть розмову</div>
            <div class="small mt-1">або натисніть ➕ щоб створити нову</div>
        </div>

        <!-- ===== PANEL 3: ROOM INFO ===== -->
        <transition name="slide-left">
            <div class="chat-info-panel" v-if="showInfo && activeRoom">
                <div class="p-3 border-bottom-subtle d-flex justify-content-between align-items-center">
                    <strong>Учасники</strong>
                    <button class="btn btn-xs btn-ghost-secondary" @click="showInfo=false">✕</button>
                </div>
                <div class="overflow-auto flex-grow-1 p-3">
                    <div v-for="m in members" :key="m.id" class="member-item d-flex align-items-center gap-2 mb-3">
                        <div class="avatar avatar-sm avatar-rounded">{{ (m.user?.username || '?')[0].toUpperCase() }}</div>
                        <div class="flex-grow-1">
                            <div>{{ m.user?.first_name || m.user?.username }}</div>
                            <div class="small text-muted">@{{ m.user?.username }}</div>
                        </div>
                        <span class="badge" :class="roleBadge(m.role)">{{ m.role }}</span>
                    </div>
                </div>
                <div class="p-3 border-top-subtle" v-if="myRole === 'owner' || myRole === 'admin'">
                    <button class="btn btn-sm btn-outline-primary w-100" @click="showInviteModal=true">+ Запросити</button>
                </div>
            </div>
        </transition>

        <!-- ===== MODALS ===== -->
        <!-- Create Room Modal -->
        <div v-if="showNewRoom" class="eme-modal-overlay" @click.self="showNewRoom=false">
            <div class="eme-modal" style="width: 400px;">
                <div class="eme-modal-header"><strong>➕ Нова кімната</strong>
                    <button class="btn btn-xs btn-ghost-secondary" @click="showNewRoom=false">✕</button>
                </div>
                <div class="eme-modal-body p-3">
                    <div class="mb-3">
                        <label class="form-label">Тип</label>
                        <div class="btn-group w-100">
                            <button class="btn btn-sm" :class="newRoom.kind==='group' ? 'btn-primary' : 'btn-ghost-secondary'" @click="newRoom.kind='group'">👥 Група</button>
                            <button class="btn btn-sm" :class="newRoom.kind==='general' ? 'btn-primary' : 'btn-ghost-secondary'" @click="newRoom.kind='general'">🌐 Загальна</button>
                        </div>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Назва</label>
                        <input class="form-control" v-model="newRoom.title" placeholder="Назва кімнати..." @keyup.enter="createRoom">
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Опис</label>
                        <input class="form-control" v-model="newRoom.description" placeholder="Опис...">
                    </div>
                </div>
                <div class="eme-modal-footer p-3 bg-transparent border-top-subtle text-end">
                    <button class="btn btn-primary" @click="createRoom">Створити</button>
                </div>
            </div>
        </div>

        <!-- Chat Settings Modal -->
        <div v-if="showSettings" class="eme-modal-overlay" @click.self="showSettings=false">
            <div class="eme-modal" style="width: 500px; max-height: 90vh; overflow-y: auto;">
                <div class="eme-modal-header"><strong>⚙️ Налаштування Чату</strong>
                    <button class="btn btn-xs btn-ghost-secondary" @click="showSettings=false">✕</button>
                </div>
                <div class="eme-modal-body p-4">
                    <h5 class="mb-3">Функції</h5>
                    <div class="mb-3 d-flex justify-content-between align-items-center">
                        <div>
                            <div class="fw-bold">😊 Стікери</div>
                            <div class="small text-muted">Надсилати стікери з відписками</div>
                        </div>
                        <div class="form-check form-switch">
                            <input class="form-check-input" type="checkbox" v-model="chatSettings.stickers_enabled" @change="saveSettings">
                        </div>
                    </div>
                    <div class="mb-4 d-flex justify-content-between align-items-center">
                        <div>
                            <div class="fw-bold">🎨 Піксель-редактор</div>
                            <div class="small text-muted">Малювати піксельні картинки 16×16</div>
                        </div>
                        <div class="form-check form-switch">
                            <input class="form-check-input" type="checkbox" v-model="chatSettings.pixel_editor_enabled" @change="saveSettings">
                        </div>
                    </div>

                    <hr class="border-subtle">
                    <h5 class="mb-3">Мої стікер-паки</h5>
                    <div v-for="pack in myPacks" :key="pack.id" class="mb-2 p-3 rounded border-subtle d-flex align-items-center gap-3" style="background: rgba(255,255,255,0.03)">
                        <div class="flex-grow-1">
                            <div class="fw-bold">{{ pack.name }}</div>
                            <div class="small text-muted">{{ pack.stickers_count }} стікерів · {{ pack.is_public ? '🌐 Публічний' : '🔒 Приватний' }}</div>
                        </div>
                        <button class="btn btn-xs btn-ghost-secondary" @click="togglePublish(pack)">
                            {{ pack.is_public ? 'Зробити приватним' : 'Опублікувати' }}
                        </button>
                    </div>

                    <button class="btn btn-outline-primary btn-sm mt-2" @click="showCreatePack=true">+ Новий пак</button>

                    <div v-if="showCreatePack" class="mt-3 p-3 rounded" style="background: rgba(255,255,255,0.03);">
                        <input class="form-control mb-2" v-model="newPackName" placeholder="Назва паку...">
                        <button class="btn btn-primary btn-sm" @click="createPack">Створити</button>
                    </div>

                    <template v-if="selectedPackForUpload">
                        <hr class="border-subtle">
                        <h6>Завантажити стікер у «{{ selectedPackForUpload.name }}»</h6>
                        <input type="text" class="form-control mb-2" v-model="newStickerLabel" placeholder="Підпис стікера...">
                        <label class="btn btn-outline-secondary btn-sm w-100">
                            📎 Вибрати зображення
                            <input type="file" accept="image/*" class="d-none" @change="uploadSticker">
                        </label>
                    </template>

                    <div class="mt-3" v-if="myPacks.length">
                        <label class="form-label small">Додати стікер до паку:</label>
                        <select class="form-select form-select-sm" v-model="selectedPackForUpload">
                            <option :value="null">Оберіть пак...</option>
                            <option v-for="p in myPacks" :key="p.id" :value="p">{{ p.name }}</option>
                        </select>
                    </div>

                    <hr class="border-subtle">
                    <h5 class="mb-3">Публічні пакети</h5>
                    <div v-for="pack in publicPacks" :key="pack.id" class="mb-2 p-3 rounded border-subtle d-flex align-items-center gap-3" style="background: rgba(255,255,255,0.03)">
                        <div class="flex-grow-1">
                            <div class="fw-bold">{{ pack.name }}</div>
                            <div class="small text-muted">{{ pack.stickers_count }} стікерів</div>
                        </div>
                        <button class="btn btn-xs btn-outline-primary" @click="activatePack(pack)">Активувати</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Invite Modal -->
        <div v-if="showInviteModal && activeRoom" class="eme-modal-overlay" @click.self="showInviteModal=false">
            <div class="eme-modal" style="width:380px;">
                <div class="eme-modal-header"><strong>Запросити до кімнати</strong>
                    <button class="btn btn-xs btn-ghost-secondary" @click="showInviteModal=false">✕</button>
                </div>
                <div class="eme-modal-body p-3">
                    <input class="form-control mb-3" v-model="inviteSearch" placeholder="Пошук користувача...">
                    <div v-for="u in filteredNetworkUsers" :key="u.id" class="d-flex align-items-center gap-2 mb-2">
                        <div class="flex-grow-1">{{ u.first_name || u.username }} <span class="text-muted small">@{{ u.username }}</span></div>
                        <button class="btn btn-xs btn-primary" @click="inviteUser(u)">Запросити</button>
                    </div>
                </div>
            </div>
        </div>

    </div>
</template>

<script>
const GRID = 16;
const CELL = 10; // pixels per cell × 160px canvas

export default {
    props: ['user', 'auth'],
    data() {
        return {
            rooms: [],
            loading: false,
            activeRoom: null,
            messages: [],
            msgsLoading: false,
            newMsg: '',
            showInfo: false,
            showNewRoom: false,
            showSettings: false,
            showInviteModal: false,
            showStickerTray: false,
            showPixelEditor: false,
            showCreatePack: false,
            members: [],
            roomSearch: '',
            inviteSearch: '',
            networkUsers: [],

            // Modals forms
            newRoom: { kind: 'group', title: '', description: '' },

            // Stickers
            chatSettings: { stickers_enabled: true, pixel_editor_enabled: false },
            myPacks: [],
            activePacks: [],
            publicPacks: [],
            activePack: null,
            selectedPackForUpload: null,
            newPackName: '',
            newStickerLabel: '',

            // Pixel editor
            pixelColor: '#00e5ff',
            pixelLabel: '',
            pixelData: Array(GRID * GRID).fill('#111422'),
            pixelPainting: false,
            PALETTE: [
                '#ffffff', '#000000', '#1a1c2e', '#5a6988', '#8ecae6',
                '#219ebc', '#023047', '#ffb703', '#fb8500', '#ff5733',
                '#00e5ff', '#00ff88', '#ff00aa', '#a855f7', '#f97316'
            ],

            polling: null,
            lastMsgCount: 0,
            mobile: window.innerWidth < 768,
        };
    },

    computed: {
        myUserId() {
            return this.user?.id;
        },
        generalRooms() {
            return this.rooms.filter(r => r.kind === 'general' && this.roomMatch(r));
        },
        dmRooms() {
            return this.rooms.filter(r => r.kind === 'dm' && this.roomMatch(r));
        },
        groupRooms() {
            return this.rooms.filter(r => r.kind === 'group' && this.roomMatch(r));
        },
        myRole() {
            if (!this.activeRoom) return null;
            const m = this.members.find(m => m.user?.id === this.myUserId);
            return m?.role || null;
        },
        filteredNetworkUsers() {
            const s = this.inviteSearch.toLowerCase();
            return this.networkUsers.filter(u =>
                u.username.toLowerCase().includes(s) ||
                (u.first_name && u.first_name.toLowerCase().includes(s))
            );
        }
    },

    methods: {
        hdrs() {
            const token = localStorage.getItem('access_token');
            return { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token };
        },
        roomMatch(r) {
            if (!this.roomSearch) return true;
            const s = this.roomSearch.toLowerCase();
            return (r.title || '').toLowerCase().includes(s);
        },
        formatTime(iso) {
            const d = new Date(iso);
            return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        },
        roleBadge(role) {
            return { owner: 'bg-danger-lt', admin: 'bg-warning-lt', member: 'bg-secondary-lt' }[role] || 'bg-secondary-lt';
        },

        // --- DATA LOADING ---
        async loadRooms() {
            this.loading = true;
            try {
                const res = await fetch('/api/chat/rooms/', { headers: this.hdrs() });
                const data = await res.json();
                this.rooms = data.results || data;
            } catch (e) { console.error(e); }
            finally { this.loading = false; }
        },
        async loadMessages() {
            if (!this.activeRoom) return;
            this.msgsLoading = this.messages.length === 0;
            try {
                const res = await fetch(`/api/chat/rooms/${this.activeRoom.id}/messages/`, { headers: this.hdrs() });
                const data = await res.json();
                const msgs = data.results || data;
                if (msgs.length !== this.lastMsgCount) {
                    this.messages = msgs;
                    this.lastMsgCount = msgs.length;
                    this.$nextTick(() => this.scrollToBottom());
                }
            } catch (e) { console.error(e); }
            finally { this.msgsLoading = false; }
        },
        async loadMembers() {
            if (!this.activeRoom) return;
            const res = await fetch(`/api/chat/rooms/${this.activeRoom.id}/members/`, { headers: this.hdrs() });
            const data = await res.json();
            this.members = data.results || data;
        },
        async loadChatSettings() {
            try {
                const res = await fetch('/api/chat/settings/', { headers: this.hdrs() });
                const data = await res.json();
                this.chatSettings = (data.results || data)[0] || this.chatSettings;
            } catch (e) { }
        },
        async loadStickers() {
            try {
                const [myRes, pubRes, activeRes] = await Promise.all([
                    fetch('/api/chat/stickerpacks/', { headers: this.hdrs() }),
                    fetch('/api/chat/stickerpacks/public/', { headers: this.hdrs() }),
                    fetch('/api/chat/stickerpacks/active/', { headers: this.hdrs() }),
                ]);
                this.myPacks = (await myRes.json()).results || await myRes.json() || [];
                this.publicPacks = (await pubRes.json()) || [];
                this.activePacks = (await activeRes.json()) || [];
                if (this.activePacks.length) this.activePack = this.activePacks[0];
            } catch(e) { console.error(e); }
        },
        async loadNetworkUsers() {
            try {
                const res = await fetch('/api/profiles/users/', { headers: this.hdrs() });
                const data = await res.json();
                this.networkUsers = data.results || data;
            } catch(e) {}
        },

        // --- ACTIONS ---
        async openRoom(room) {
            this.activeRoom = room;
            this.messages = [];
            this.lastMsgCount = 0;
            this.showStickerTray = false;
            this.showPixelEditor = false;
            await this.loadMessages();
            await this.loadMembers();
            if (this.polling) clearInterval(this.polling);
            this.polling = setInterval(() => this.loadMessages(), 4000);
        },

        async sendText() {
            if (!this.newMsg.trim() || !this.activeRoom) return;
            const text = this.newMsg.trim();
            this.newMsg = '';
            this.$nextTick(() => { if (this.$refs.msgInput) this.$refs.msgInput.style.height = 'auto'; });
            await fetch(`/api/chat/rooms/${this.activeRoom.id}/messages/`, {
                method: 'POST', headers: this.hdrs(),
                body: JSON.stringify({ msg_type: 'text', text })
            });
            await this.loadMessages();
        },

        async sendSticker(sticker) {
            if (!this.activeRoom) return;
            await fetch(`/api/chat/rooms/${this.activeRoom.id}/messages/`, {
                method: 'POST', headers: this.hdrs(),
                body: JSON.stringify({ msg_type: 'sticker', sticker: sticker.id, text: sticker.label || '' })
            });
            this.showStickerTray = false;
            await this.loadMessages();
        },

        async attachFile(evt) {
            const file = evt.target.files[0];
            if (!file) return;
            const fd = new FormData();
            fd.append('file', file);
            try {
                const res = await fetch('/api/media/upload/', {
                    method: 'POST',
                    headers: { 'Authorization': this.hdrs().Authorization },
                    body: fd
                });
                if (!res.ok) { alert('Upload error'); return; }
                const mediaFile = await res.json();
                const isImage = file.type.startsWith('image/');
                await fetch(`/api/chat/rooms/${this.activeRoom.id}/messages/`, {
                    method: 'POST', headers: this.hdrs(),
                    body: JSON.stringify({ msg_type: isImage ? 'image' : 'file', attachment: mediaFile.id })
                });
                await this.loadMessages();
            } catch(e) { console.error(e); }
            evt.target.value = '';
        },

        async sendPixelArt() {
            const canvas = this.$refs.pixelCanvas;
            if (!canvas) return;
            canvas.toBlob(async (blob) => {
                const fd = new FormData();
                fd.append('file', blob, `pixel_${Date.now()}.png`);
                const res = await fetch('/api/media/upload/', {
                    method: 'POST',
                    headers: { 'Authorization': this.hdrs().Authorization },
                    body: fd
                });
                const mediaFile = await res.json();
                // Save as sticker in a "Pixel Art" temp pack, then send
                await fetch(`/api/chat/rooms/${this.activeRoom.id}/messages/`, {
                    method: 'POST', headers: this.hdrs(),
                    body: JSON.stringify({ msg_type: 'image', attachment: mediaFile.id, text: this.pixelLabel })
                });
                this.showPixelEditor = false;
                this.clearCanvas();
                await this.loadMessages();
            }, 'image/png');
        },

        async createRoom() {
            if (!this.newRoom.title.trim()) return;
            const res = await fetch('/api/chat/rooms/', {
                method: 'POST', headers: this.hdrs(),
                body: JSON.stringify(this.newRoom)
            });
            if (res.ok) {
                this.showNewRoom = false;
                this.newRoom = { kind: 'group', title: '', description: '' };
                await this.loadRooms();
            }
        },

        async inviteUser(u) {
            if (!this.activeRoom) return;
            await fetch(`/api/chat/rooms/${this.activeRoom.id}/invite/`, {
                method: 'POST', headers: this.hdrs(),
                body: JSON.stringify({ user_id: u.id })
            });
            this.showInviteModal = false;
            await this.loadMembers();
        },

        async saveSettings() {
            await fetch('/api/chat/settings/', {
                method: 'POST', headers: this.hdrs(),
                body: JSON.stringify(this.chatSettings)
            });
        },

        async createPack() {
            if (!this.newPackName.trim()) return;
            const res = await fetch('/api/chat/stickerpacks/', {
                method: 'POST', headers: this.hdrs(),
                body: JSON.stringify({ name: this.newPackName })
            });
            if (res.ok) {
                this.newPackName = '';
                this.showCreatePack = false;
                await this.loadStickers();
            }
        },

        async togglePublish(pack) {
            await fetch(`/api/chat/stickerpacks/${pack.id}/publish/`, {
                method: 'POST', headers: this.hdrs()
            });
            await this.loadStickers();
        },

        async activatePack(pack) {
            await fetch(`/api/chat/stickerpacks/${pack.id}/activate/`, {
                method: 'POST', headers: this.hdrs()
            });
            await this.loadStickers();
        },

        async uploadSticker(evt) {
            if (!this.selectedPackForUpload) return;
            const file = evt.target.files[0];
            if (!file) return;
            const fd = new FormData();
            fd.append('file', file);
            const uploadRes = await fetch('/api/media/upload/', {
                method: 'POST',
                headers: { 'Authorization': this.hdrs().Authorization },
                body: fd
            });
            const mediaFile = await uploadRes.json();
            await fetch(`/api/chat/stickerpacks/${this.selectedPackForUpload.id}/add_sticker/`, {
                method: 'POST', headers: this.hdrs(),
                body: JSON.stringify({ image: mediaFile.id, label: this.newStickerLabel })
            });
            this.newStickerLabel = '';
            await this.loadStickers();
            evt.target.value = '';
        },

        // --- PIXEL EDITOR ---
        drawPixel(evt) {
            const { col, row } = this.getCell(evt, this.$refs.pixelCanvas);
            this.pixelData[row * GRID + col] = this.pixelColor;
            this.renderCanvas();
        },
        drawPixelTouch(evt) {
            const touch = evt.touches[0];
            const { col, row } = this.getCell(touch, this.$refs.pixelCanvas);
            this.pixelData[row * GRID + col] = this.pixelColor;
            this.renderCanvas();
        },
        getCell(evt, canvas) {
            const rect = canvas.getBoundingClientRect();
            const scaleX = canvas.width / rect.width;
            const scaleY = canvas.height / rect.height;
            const x = (evt.clientX - rect.left) * scaleX;
            const y = (evt.clientY - rect.top) * scaleY;
            return { col: Math.floor(x / CELL), row: Math.floor(y / CELL) };
        },
        renderCanvas() {
            const canvas = this.$refs.pixelCanvas;
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            for (let r = 0; r < GRID; r++) {
                for (let c = 0; c < GRID; c++) {
                    ctx.fillStyle = this.pixelData[r * GRID + c];
                    ctx.fillRect(c * CELL, r * CELL, CELL, CELL);
                }
            }
        },
        clearCanvas() {
            this.pixelData = Array(GRID * GRID).fill('#111422');
            this.renderCanvas();
        },

        scrollToBottom() {
            const el = this.$refs.msgList;
            if (el) el.scrollTop = el.scrollHeight;
        },
        autoGrow() {
            const el = this.$refs.msgInput;
            if (!el) return;
            el.style.height = 'auto';
            el.style.height = Math.min(el.scrollHeight, 120) + 'px';
        }
    },

    async mounted() {
        await this.loadRooms();
        await this.loadChatSettings();
        await this.loadStickers();
        await this.loadNetworkUsers();
        this.$nextTick(() => {
            if (this.$refs.pixelCanvas) this.renderCanvas();
        });
    },
    beforeUnmount() {
        if (this.polling) clearInterval(this.polling);
    },
    watch: {
        showPixelEditor(v) {
            if (v) this.$nextTick(() => this.renderCanvas());
        }
    }
}
</script>

<style scoped>
.chat-shell {
    background: #0d0f1a;
    color: #e2e8f0;
    overflow: hidden;
}

/* SIDEBAR */
.chat-sidebar {
    width: 280px;
    min-width: 260px;
    background: rgba(18, 20, 34, 0.9);
    border-right: 1px solid rgba(255,255,255,0.05);
    backdrop-filter: blur(12px);
    transition: width .3s;
}
.chat-sidebar.collapsed { width: 0; min-width: 0; overflow: hidden; }

.chat-sidebar-header {
    background: rgba(0,229,255,0.04);
    border-bottom: 1px solid rgba(255,255,255,0.05);
}

.room-section-label {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #4a5568;
}

.room-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 12px;
    cursor: pointer;
    border-radius: 10px;
    margin: 2px 8px;
    transition: background .15s;
}
.room-item:hover { background: rgba(255,255,255,0.04); }
.room-item.active { background: rgba(0,229,255,0.08); border: 1px solid rgba(0,229,255,0.15); }
.room-avatar { font-size: 1.5rem; width: 36px; text-align: center; flex-shrink: 0; }
.room-name { font-size: .9rem; font-weight: 600; }
.room-preview { font-size: .75rem; color: #64748b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 160px; }

/* MAIN AREA */
.chat-main { background: #0d0f1a; }
.chat-main-header {
    background: rgba(18, 20, 34, 0.8);
    border-bottom: 1px solid rgba(255,255,255,0.05);
    backdrop-filter: blur(8px);
}
.room-avatar-lg { font-size: 2rem; }

.chat-messages { padding-bottom: 1rem; }

.msg-row {
    display: flex;
    gap: 8px;
    margin-bottom: 12px;
    align-items: flex-end;
}
.msg-row--mine { flex-direction: row-reverse; }

.msg-avatar {
    width: 32px; height: 32px;
    border-radius: 50%;
    background: rgba(0,229,255,0.15);
    color: #00e5ff;
    display: flex; align-items: center; justify-content: center;
    font-size: .8rem; font-weight: 700;
    flex-shrink: 0;
}
.msg-bubble-wrap { max-width: 70%; }
.msg-name { margin-left: 4px; }

.msg-bubble {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 16px 16px 16px 4px;
    padding: 10px 14px;
    font-size: .9rem;
    line-height: 1.5;
    word-break: break-word;
}
.msg-bubble--mine {
    background: rgba(0,229,255,0.12);
    border-color: rgba(0,229,255,0.2);
    border-radius: 16px 16px 4px 16px;
}
.msg-bubble--file .file-link {
    color: #00e5ff;
    text-decoration: none;
    font-weight: 500;
}
.msg-image-preview { max-width: 200px; border-radius: 8px; display: block; margin-top: 6px; }

.msg-sticker { padding: 4px; }
.sticker-img { max-width: 120px; max-height: 120px; border-radius: 8px; display: block; }
.sticker-label { font-size:.75rem; color:#64748b; margin-top:4px; text-align:center; }
.msg-time { font-size: .7rem; color: #4a5568; margin-top: 4px; text-align: right; }

/* MESSAGE INPUT */
.chat-input-bar {
    background: rgba(18,20,34,0.95);
    border-top: 1px solid rgba(255,255,255,0.05);
    backdrop-filter: blur(8px);
}
.chat-textarea {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    color: #e2e8f0;
    border-radius: 12px;
    resize: none;
    overflow-y: auto;
    min-height: 38px;
}
.chat-textarea:focus {
    background: rgba(255,255,255,0.07);
    border-color: rgba(0,229,255,0.3);
    box-shadow: 0 0 0 3px rgba(0,229,255,0.07);
    color: white;
}

/* STICKER TRAY */
.sticker-tray {
    background: rgba(15,17,30,0.98);
    border-top: 1px solid rgba(255,255,255,0.05);
    max-height: 220px;
    overflow-y: auto;
}
.sticker-grid { display: flex; flex-wrap: wrap; gap: 8px; padding: 4px 0; }
.sticker-cell { cursor: pointer; text-align: center; border-radius: 8px; padding: 4px; transition: background .15s; }
.sticker-cell:hover { background: rgba(0,229,255,0.08); }
.sticker-thumb { width: 64px; height: 64px; object-fit: contain; display: block; border-radius: 6px; }
.sticker-cell-label { font-size: .65rem; color: #64748b; margin-top: 2px; max-width: 64px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* PIXEL EDITOR */
.pixel-editor-tray {
    background: rgba(15,17,30,0.98);
    border-top: 1px solid rgba(255,255,255,0.05);
}
.pixel-canvas {
    image-rendering: pixelated;
    border: 1px solid rgba(0,229,255,0.2);
    border-radius: 6px;
    cursor: crosshair;
    width: 160px; height: 160px;
}
.color-cell {
    width: 22px; height: 22px;
    border-radius: 4px;
    cursor: pointer;
    border: 2px solid transparent;
    transition: transform .1s;
}
.color-cell.active, .color-cell:hover { border-color: white; transform: scale(1.15); }

/* ROOM INFO PANEL */
.chat-info-panel {
    width: 260px;
    flex-shrink: 0;
    background: rgba(18,20,34,0.9);
    border-left: 1px solid rgba(255,255,255,0.05);
    display: flex; flex-direction: column;
    backdrop-filter: blur(8px);
}
.member-item { padding: 4px 0; }

/* TRANSITIONS */
.slide-up-enter-active, .slide-up-leave-active { transition: max-height .25s ease, opacity .2s; }
.slide-up-enter-from, .slide-up-leave-to { max-height: 0; opacity: 0; }
.slide-up-enter-to, .slide-up-leave-from { max-height: 250px; opacity: 1; }

.slide-left-enter-active, .slide-left-leave-active { transition: width .25s ease; }
.slide-left-enter-from, .slide-left-leave-to { width: 0; }
.slide-left-enter-to, .slide-left-leave-from { width: 260px; }

/* Form overrides for dark theme */
.form-control, .form-select, .form-check-input {
    background: rgba(255,255,255,0.05);
    border-color: rgba(255,255,255,0.1);
    color: #e2e8f0;
}
.form-control:focus, .form-select:focus {
    background: rgba(255,255,255,0.08);
    border-color: rgba(0,229,255,0.4);
    box-shadow: 0 0 0 3px rgba(0,229,255,0.08);
    color: white;
}
.form-control::placeholder { color: #4a5568; }

@media (max-width: 768px) {
    .chat-sidebar { width: 100%; border-right: none; }
    .chat-info-panel { display: none; }
}
</style>
